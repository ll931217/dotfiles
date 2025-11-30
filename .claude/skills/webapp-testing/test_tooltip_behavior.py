"""
Test tooltip hide/show behavior for candlestick and volume charts.

This script tests:
1. Candlestick tooltip appears on hover
2. Candlestick tooltip hides when cursor leaves chart
3. Volume tooltip appears on hover
4. Volume tooltip hides when cursor leaves chart
5. No tooltips remain visible after cursor exits
"""

from playwright.sync_api import sync_playwright
import time

def test_tooltip_behavior():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use headed mode to see what happens
        page = browser.new_page()

        print("Navigating to http://localhost:3000/lightweight/2330...")
        page.goto('http://localhost:3000/lightweight/2330')
        page.wait_for_load_state('networkidle')

        print("Waiting for charts to initialize...")
        time.sleep(2)  # Give charts time to render

        # Take initial screenshot
        page.screenshot(path='/tmp/tooltip_test_initial.png', full_page=True)
        print("Initial screenshot saved to /tmp/tooltip_test_initial.png")

        # Find the chart containers
        print("\n1. Testing candlestick tooltip...")

        # Get chart container dimensions
        chart_container = page.locator('[data-testid="candlestick-chart"]').first
        if not chart_container.is_visible():
            print("ERROR: Chart container not found!")
            browser.close()
            return

        # Get bounding box of chart
        bbox = chart_container.bounding_box()
        if not bbox:
            print("ERROR: Could not get chart bounding box!")
            browser.close()
            return

        print(f"Chart container found at: x={bbox['x']}, y={bbox['y']}, width={bbox['width']}, height={bbox['height']}")

        # Move cursor to center of main chart area (60% height for candlestick chart)
        chart_center_x = bbox['x'] + bbox['width'] / 2
        chart_center_y = bbox['y'] + bbox['height'] * 0.3  # Middle of candlestick chart area

        print(f"Moving cursor to candlestick chart center: ({chart_center_x}, {chart_center_y})")
        page.mouse.move(chart_center_x, chart_center_y)
        time.sleep(0.5)

        # Take screenshot with tooltip (should be visible)
        page.screenshot(path='/tmp/tooltip_test_candlestick_hover.png', full_page=True)
        print("Screenshot with candlestick tooltip saved to /tmp/tooltip_test_candlestick_hover.png")

        # Check if candlestick tooltip is visible
        candlestick_tooltip = page.locator('.candlestick-tooltip').first
        is_visible = candlestick_tooltip.is_visible() if candlestick_tooltip.count() > 0 else False
        print(f"Candlestick tooltip visible: {is_visible}")

        # Move cursor outside chart area
        print("\n2. Testing candlestick tooltip hide...")
        page.mouse.move(bbox['x'] - 50, bbox['y'] - 50)
        time.sleep(0.3)

        # Take screenshot (tooltip should be hidden)
        page.screenshot(path='/tmp/tooltip_test_candlestick_hide.png', full_page=True)
        print("Screenshot after leaving candlestick chart saved to /tmp/tooltip_test_candlestick_hide.png")

        # Check if tooltip is hidden
        is_visible_after = candlestick_tooltip.is_visible() if candlestick_tooltip.count() > 0 else False
        print(f"Candlestick tooltip visible after leaving: {is_visible_after}")

        # Test volume chart tooltip
        print("\n3. Testing volume tooltip...")
        volume_center_y = bbox['y'] + bbox['height'] * 0.8  # Middle of volume chart area

        print(f"Moving cursor to volume chart center: ({chart_center_x}, {volume_center_y})")
        page.mouse.move(chart_center_x, volume_center_y)
        time.sleep(0.5)

        # Take screenshot with volume tooltip
        page.screenshot(path='/tmp/tooltip_test_volume_hover.png', full_page=True)
        print("Screenshot with volume tooltip saved to /tmp/tooltip_test_volume_hover.png")

        # Check if volume tooltip is visible
        volume_tooltip = page.locator('.volume-tooltip').first
        is_volume_visible = volume_tooltip.is_visible() if volume_tooltip.count() > 0 else False
        print(f"Volume tooltip visible: {is_volume_visible}")

        # Move cursor outside chart area again
        print("\n4. Testing volume tooltip hide...")
        page.mouse.move(bbox['x'] - 50, bbox['y'] - 50)
        time.sleep(0.3)

        # Take screenshot (both tooltips should be hidden)
        page.screenshot(path='/tmp/tooltip_test_volume_hide.png', full_page=True)
        print("Screenshot after leaving volume chart saved to /tmp/tooltip_test_volume_hide.png")

        # Check if both tooltips are hidden
        is_volume_visible_after = volume_tooltip.is_visible() if volume_tooltip.count() > 0 else False
        is_candlestick_visible_after = candlestick_tooltip.is_visible() if candlestick_tooltip.count() > 0 else False

        print(f"Volume tooltip visible after leaving: {is_volume_visible_after}")
        print(f"Candlestick tooltip visible after leaving: {is_candlestick_visible_after}")

        # Test rapid movement between charts
        print("\n5. Testing rapid movement between charts...")
        for i in range(3):
            # Move to candlestick chart
            page.mouse.move(chart_center_x, chart_center_y)
            time.sleep(0.2)

            # Move to volume chart
            page.mouse.move(chart_center_x, volume_center_y)
            time.sleep(0.2)

        # Move outside
        page.mouse.move(bbox['x'] - 50, bbox['y'] - 50)
        time.sleep(0.3)

        page.screenshot(path='/tmp/tooltip_test_rapid_movement.png', full_page=True)
        print("Screenshot after rapid movement saved to /tmp/tooltip_test_rapid_movement.png")

        # Final check - no tooltips should be visible
        final_candlestick_visible = candlestick_tooltip.is_visible() if candlestick_tooltip.count() > 0 else False
        final_volume_visible = volume_tooltip.is_visible() if volume_tooltip.count() > 0 else False

        print(f"\nFinal state - Candlestick tooltip visible: {final_candlestick_visible}")
        print(f"Final state - Volume tooltip visible: {final_volume_visible}")

        # Print summary
        print("\n" + "="*60)
        print("TOOLTIP BEHAVIOR TEST SUMMARY")
        print("="*60)
        print(f"✓ Candlestick tooltip appears on hover: {is_visible}")
        print(f"✓ Candlestick tooltip hides on leave: {not is_visible_after}")
        print(f"✓ Volume tooltip appears on hover: {is_volume_visible}")
        print(f"✓ Volume tooltip hides on leave: {not is_volume_visible_after}")
        print(f"✓ No tooltips after rapid movement: {not final_candlestick_visible and not final_volume_visible}")

        all_tests_pass = (
            is_visible and
            not is_visible_after and
            is_volume_visible and
            not is_volume_visible_after and
            not final_candlestick_visible and
            not final_volume_visible
        )

        if all_tests_pass:
            print("\n✅ ALL TESTS PASSED - Tooltip behavior is correct!")
        else:
            print("\n❌ SOME TESTS FAILED - Review screenshots for details")

        print("="*60)

        browser.close()

if __name__ == "__main__":
    test_tooltip_behavior()
