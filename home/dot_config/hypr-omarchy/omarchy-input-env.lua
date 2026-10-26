-- Adapted from omacom/omarchy default/hypr/{input,envs}.lua at 967bbdd7346e.
for name, value in pairs({
  XCURSOR_SIZE = "24",
  HYPRCURSOR_SIZE = "24",
  GTK_IM_MODULE = "fcitx",
  QT_IM_MODULE = "fcitx",
  XMODIFIERS = "@im=fcitx",
  GDK_BACKEND = "wayland,x11,*",
  QT_QPA_PLATFORM = "wayland;xcb",
  MOZ_ENABLE_WAYLAND = "1",
  ELECTRON_OZONE_PLATFORM_HINT = "wayland",
  OZONE_PLATFORM = "wayland",
  XDG_SESSION_TYPE = "wayland",
  XDG_CURRENT_DESKTOP = "Hyprland",
  XDG_SESSION_DESKTOP = "Hyprland",
}) do
  hl.env(name, value)
end

hl.config({
  input = {
    kb_layout = "us",
    follow_mouse = 1,
    sensitivity = 0,
    repeat_rate = 40,
    repeat_delay = 250,
    numlock_by_default = true,
    touchpad = {
      natural_scroll = false,
      clickfinger_behavior = true,
      scroll_factor = 0.4,
    },
  },
  misc = {
    key_press_enables_dpms = true,
    mouse_move_enables_dpms = true,
  },
  xwayland = { force_zero_scaling = true },
})
