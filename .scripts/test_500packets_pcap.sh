#!/bin/bash

# echo '1qaz@WSX' | sudo -S nohup taskset -c 3 tcpreplay -i X40-Quote-Gen -x 1 --timer=nano /home/vici/cas/20250623_All_Quote_500packets.pcap > /dev/null &

#nics=('X40-TWSE-Q' 'X40-Taifex-Q' 'X40-VEX-Report' 'X40-Order')

#for nic in "${nics[@]}"; do
#	echo '1qaz@WSX' | sudo -S timeout 5 tcpdump -i "$nic" -c 20 -nn
#done

# Configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="/var/log/${SCRIPT_NAME%.sh}.log"
readonly PCAP_FILE="/home/vici/cas/20250623_All_Quote_500packets.pcap"
readonly QUOTE_GEN_NIC="X40-Quote-Gen"
readonly CPU_CORE=3

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

#!/bin/bash

#NICS=('X40-TWSE-Q' 'X40-Taifex-Q' 'X40-VEX-Report' 'X40-Order')
NICS=()
TCPDUMP_TIMEOUT=5
TCPDUMP_PACKET_COUNT=20
CAPTURE_METHOD="concurrent"

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -i, --interfaces IFACE1 IFACE2 ...    Network interfaces to monitor (space-separated)
    -t, --timeout SECONDS                 Timeout for tcpdump (default: $TCPDUMP_TIMEOUT)
    -c, --count PACKETS                   Number of packets to capture per interface (default: $TCPDUMP_PACKET_COUNT)
    -m, --method METHOD                   Capture method: sequential|concurrent|advanced|parallel (default: $CAPTURE_METHOD)
    -h, --help                           Show this help message

Examples:
    $0 -i eth0 eth1 wlan0
    $0 --interfaces eth0 eth1 --timeout 10 --count 20
    $0 -i eth0 eth1 -m parallel -t 15

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interfaces)
                shift
                # Collect all interfaces until next option or end
                while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
                    NICS+=("$1")
                    shift
                done
                ;;
            -t|--timeout)
                if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                    TCPDUMP_TIMEOUT="$2"
                    shift 2
                else
                    log "ERROR" "Invalid timeout value: $2"
                    exit 1
                fi
                ;;
            -c|--count)
                if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                    TCPDUMP_PACKET_COUNT="$2"
                    shift 2
                else
                    log "ERROR" "Invalid packet count value: $2"
                    exit 1
                fi
                ;;
            -m|--method)
                if [[ "$2" =~ ^(sequential|concurrent|advanced|parallel)$ ]]; then
                    CAPTURE_METHOD="$2"
                    shift 2
                else
                    log "ERROR" "Invalid capture method: $2"
                    exit 1
                fi
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                log "ERROR" "Unexpected argument: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Logging function
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR" "$1"
    exit 1
}

# Check if running as root or with sudo access
check_privileges() {
    if [[ $EUID -eq 0 ]]; then
        log "INFO" "Running as root"
        SUDO_CMD=""
    elif sudo -n true 2>/dev/null; then
        log "INFO" "Sudo access available"
        SUDO_CMD="sudo"
    else
        error_exit "This script requires root privileges or sudo access"
    fi
}

# Validate network interface exists
validate_interface() {
    local interface="$1"
    if ! ip link show "$interface" &>/dev/null; then
        log "WARN" "Interface $interface not found"
        return 1
    fi
    return 0
}

# Validate required files and commands
validate_dependencies() {
    local missing_deps=()

    # Check required commands
    for cmd in tcpreplay tcpdump taskset timeout; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error_exit "Missing required commands: ${missing_deps[*]}"
    fi

    # Check PCAP file
    if [[ ! -f "$PCAP_FILE" ]]; then
        error_exit "PCAP file not found: $PCAP_FILE"
    fi

    # Check CPU core exists
    local max_cpu=$(($(nproc) - 1))
    if [[ $CPU_CORE -gt $max_cpu ]]; then
        error_exit "CPU core $CPU_CORE doesn't exist (max: $max_cpu)"
    fi
}

# Start tcpreplay with proper error handling
start_tcpreplay() {
    log "INFO" "Starting tcpreplay on interface $QUOTE_GEN_NIC"

    if ! validate_interface "$QUOTE_GEN_NIC"; then
        error_exit "Cannot start tcpreplay: interface $QUOTE_GEN_NIC not available"
    fi

    # Create a more robust background process
    local tcpreplay_cmd="taskset -c $CPU_CORE tcpreplay -i $QUOTE_GEN_NIC -x 1 --timer=nano $PCAP_FILE"

    if $SUDO_CMD nohup $tcpreplay_cmd >"$LOG_FILE.tcpreplay" 2>&1 &
    then
        local tcpreplay_pid=$!
        echo "$tcpreplay_pid" > "/tmp/${SCRIPT_NAME}_tcpreplay.pid"
        log "INFO" "Tcpreplay started successfully (PID: $tcpreplay_pid)"
    else
        error_exit "Failed to start tcpreplay"
    fi
}

# Capture packets from network interfaces (Sequentially)
capture_packets() {
    log "INFO" "Starting packet capture on ${#NICS[@]} interfaces"

    local failed_interfaces=()

    for nic in "${NICS[@]}"; do
        printf "${YELLOW}Capturing from interface: %s${NC}\n" "$nic"

        if ! validate_interface "$nic"; then
            failed_interfaces+=("$nic")
            continue
        fi

        log "INFO" "Capturing $TCPDUMP_PACKET_COUNT packets from $nic (timeout: ${TCPDUMP_TIMEOUT}s)"

        if $SUDO_CMD timeout "$TCPDUMP_TIMEOUT" tcpdump -i "$nic" -c "$TCPDUMP_PACKET_COUNT" -vv -nn; then
            log "INFO" "Successfully captured from $nic"
        else
            local exit_code=$?
            if [[ $exit_code -eq 124 ]]; then
                log "WARN" "Timeout reached for interface $nic"
            else
                log "ERROR" "Failed to capture from $nic (exit code: $exit_code)"
                failed_interfaces+=("$nic")
            fi
        fi
        echo # Add blank line for readability
    done

    if [[ ${#failed_interfaces[@]} -gt 0 ]]; then
        log "WARN" "Failed interfaces: ${failed_interfaces[*]}"
    fi
}

# Capture packets from network interfaces concurrently
capture_packets_concurrent() {
    log "INFO" "Starting concurrent packet capture on ${#NICS[@]} interfaces"

    local pids=()
    local failed_interfaces=()
    local temp_dir="/tmp/${SCRIPT_NAME}_capture"

    # Create temporary directory for output files
    mkdir -p "$temp_dir"

    # Start all tcpdump processes in background
    for nic in "${NICS[@]}"; do
        if ! validate_interface "$nic"; then
            failed_interfaces+=("$nic")
            continue
        fi

        log "INFO" "Starting capture on $nic"

        # Run tcpdump in background, save output to temp file
        (
            if $SUDO_CMD timeout "$TCPDUMP_TIMEOUT" tcpdump -i "$nic" -c "$TCPDUMP_PACKET_COUNT" -vv -nn \
                > "$temp_dir/${nic}.out" 2> "$temp_dir/${nic}.err"; then
                echo "SUCCESS:$nic" > "$temp_dir/${nic}.status"
            else
                local exit_code=$?
                echo "FAILED:$nic:$exit_code" > "$temp_dir/${nic}.status"
            fi
        ) &

        pids+=($!)
    done

    log "INFO" "Started ${#pids[@]} concurrent tcpdump processes"

    # Wait for all processes to complete
    for pid in "${pids[@]}"; do
        wait "$pid"
    done

    # Process results
    display_capture_results "$temp_dir"

    # Cleanup
    rm -rf "$temp_dir"

    if [[ ${#failed_interfaces[@]} -gt 0 ]]; then
        log "WARN" "Failed interfaces: ${failed_interfaces[*]}"
    fi
}

# Display results from concurrent captures
display_capture_results() {
    local temp_dir="$1"

    echo -e "\n${GREEN}=== Capture Results ===${NC}"

    for nic in "${NICS[@]}"; do
        local status_file="$temp_dir/${nic}.status"
        local output_file="$temp_dir/${nic}.out"
        local error_file="$temp_dir/${nic}.err"

        if [[ -f "$status_file" ]]; then
            local status
            status=$(cat "$status_file")

            if [[ $status == SUCCESS:* ]]; then
                printf "${GREEN}✓ %s${NC}\n" "$nic"
                if [[ -f "$output_file" && -s "$output_file" ]]; then
                    echo "  Output:"
                    sed 's/^/    /' "$output_file"
                fi
            else
                printf "${RED}✗ %s${NC}\n" "$nic"
                if [[ -f "$error_file" && -s "$error_file" ]]; then
                    echo "  Error:"
                    sed 's/^/    /' "$error_file"
                fi
            fi
        else
            printf "${YELLOW}? %s (no status)${NC}\n" "$nic"
        fi
        echo
    done
}

cleanup() {
    log "INFO" "Cleaning up..."

    # Kill tcpreplay if still running
    local pid_file="/tmp/${SCRIPT_NAME}_tcpreplay.pid"
    if [[ -f "$pid_file" ]]; then
        local tcpreplay_pid
        tcpreplay_pid=$(cat "$pid_file")
        if kill -0 "$tcpreplay_pid" 2>/dev/null; then
            log "INFO" "Stopping tcpreplay (PID: $tcpreplay_pid)"
            $SUDO_CMD kill "$tcpreplay_pid"
        fi
        rm -f "$pid_file"
    fi
}

# Signal handlers
trap cleanup EXIT
trap 'error_exit "Script interrupted"' INT TERM

# Main execution
main() {
    log "INFO" "Starting $SCRIPT_NAME"

    parse_arguments "$@"

    check_privileges
    validate_dependencies

    start_tcpreplay

    # Small delay to let tcpreplay start
    sleep 2

    # capture_packets
    capture_packets_concurrent

    log "INFO" "Script completed successfully"
}

main "$@"
