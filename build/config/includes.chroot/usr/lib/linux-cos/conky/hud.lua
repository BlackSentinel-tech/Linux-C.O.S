-- Linux-C.O.S desktop HUD (conky + Lua/Cairo). Colours come from the active
-- mode via ~/.config/linux-cos/conky/palette.lua (written by `cos session`).
require 'cairo'
require 'cairo_xlib'

local home = os.getenv("HOME") or ""
local ok, P = pcall(dofile, home .. "/.config/linux-cos/conky/palette.lua")
if not ok or type(P) ~= "table" then
  P = { accent = "#00e5ff", accent2 = "#ff2e63", fg = "#e8eeff", dim = "#7f8db8", bg = "#060914", ok = "#2dff9d", warn = "#ffc857", bad = "#ff2e63", mode = "dual" }
end

local function rgb(hex, a)
  hex = hex:gsub("#", "")
  return tonumber(hex:sub(1, 2), 16) / 255, tonumber(hex:sub(3, 4), 16) / 255, tonumber(hex:sub(5, 6), 16) / 255, a or 1
end

local function color(cr, hex, a) cairo_set_source_rgba(cr, rgb(hex, a)) end

local function text(cr, s, x, y, size, hex, a, bold, family, align)
  cairo_select_font_face(cr, family or "Inter", CAIRO_FONT_SLANT_NORMAL, bold and CAIRO_FONT_WEIGHT_BOLD or CAIRO_FONT_WEIGHT_NORMAL)
  cairo_set_font_size(cr, size)
  local ext = cairo_text_extents_t:create()
  cairo_text_extents(cr, s, ext)
  if align == "right" then x = x - ext.width - ext.x_bearing elseif align == "center" then x = x - ext.width / 2 - ext.x_bearing end
  color(cr, hex, a)
  cairo_move_to(cr, x, y)
  cairo_show_text(cr, s)
  return ext.width
end

local function ring(cr, cx, cy, r, frac, hex, label, value)
  frac = math.max(0, math.min(1, frac))
  local a0 = -math.pi / 2
  cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
  -- track
  cairo_set_line_width(cr, 6)
  color(cr, hex, 0.14)
  cairo_arc(cr, cx, cy, r, 0, 2 * math.pi)
  cairo_stroke(cr)
  -- glow + value
  if frac > 0.002 then
    for _, g in ipairs({ { 14, 0.07 }, { 10, 0.12 }, { 6, 1.0 } }) do
      cairo_set_line_width(cr, g[1])
      color(cr, hex, g[2])
      cairo_arc(cr, cx, cy, r, a0, a0 + 2 * math.pi * frac)
      cairo_stroke(cr)
    end
  end
  -- ticks
  cairo_set_line_width(cr, 1)
  for i = 0, 35 do
    local ang = i * math.pi / 18
    local r0, r1 = r + 10, r + (i % 3 == 0 and 15 or 12)
    color(cr, P.dim, i % 3 == 0 and 0.55 or 0.25)
    cairo_move_to(cr, cx + r0 * math.cos(ang), cy + r0 * math.sin(ang))
    cairo_line_to(cr, cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))
    cairo_stroke(cr)
  end
  text(cr, value, cx, cy + 6, 17, P.fg, 1, true, "Oxanium", "center")
  text(cr, label, cx, cy + r + 30, 11, P.dim, 1, false, "JetBrains Mono", "center")
end

local function bar(cr, x, y, w, frac, hex)
  frac = math.max(0, math.min(1, frac))
  color(cr, hex, 0.15); cairo_rectangle(cr, x, y, w, 4); cairo_fill(cr)
  color(cr, hex, 0.35); cairo_rectangle(cr, x, y - 1, w * frac, 6); cairo_fill(cr)
  color(cr, hex, 1); cairo_rectangle(cr, x, y, w * frac, 4); cairo_fill(cr)
end

local function fmt_speed(kib)
  if kib > 1024 then return string.format("%.1f MB/s", kib / 1024) end
  return string.format("%.0f KB/s", kib)
end

local function num(s) return tonumber((conky_parse(s) or ""):match("[%d%.]+")) or 0 end

function conky_cos_hud()
  if conky_window == nil then return end
  local cs = cairo_xlib_surface_create(conky_window.display, conky_window.drawable, conky_window.visual, conky_window.width, conky_window.height)
  local cr = cairo_create(cs)
  local W = conky_window.width

  -- header
  text(cr, "LINUX-C.O.S", 0, 18, 12, P.accent, 1, true, "Oxanium")
  local chip = (P.mode == "red" and "RED TEAM") or (P.mode == "blue" and "BLUE TEAM") or "DUAL"
  text(cr, chip, W, 18, 11, P.accent2, 1, true, "JetBrains Mono", "right")
  color(cr, P.accent, 0.5); cairo_set_line_width(cr, 1); cairo_move_to(cr, 0, 28); cairo_line_to(cr, W, 28); cairo_stroke(cr)

  -- clock
  text(cr, os.date("%H:%M"), 0, 100, 76, P.fg, 1, true, "Oxanium")
  text(cr, os.date("%S"), W, 100, 26, P.accent, 1, true, "Oxanium", "right")
  text(cr, string.upper(os.date("%A  %d %B %Y")), 0, 126, 12, P.dim, 1, false, "JetBrains Mono")

  -- gauges
  local cpu, mem, disk = num("${cpu cpu0}"), num("${memperc}"), num("${fs_used_perc /}")
  ring(cr, 52, 205, 36, cpu / 100, P.accent, "CPU", string.format("%d%%", cpu))
  ring(cr, 170, 205, 36, mem / 100, P.accent2, "RAM", string.format("%d%%", mem))
  ring(cr, 288, 205, 36, disk / 100, P.warn, "DISK", string.format("%d%%", disk))

  -- network
  local iface = conky_parse("${gw_iface}")
  iface = (iface == nil or iface == "" or iface:match("^%s*$")) and "lo" or iface:gsub("%s+", "")
  local down, up = num("${downspeedf " .. iface .. "}"), num("${upspeedf " .. iface .. "}")
  text(cr, "NETWORK", 0, 300, 11, P.dim, 1, true, "JetBrains Mono")
  text(cr, iface, W, 300, 11, P.dim, 1, false, "JetBrains Mono", "right")
  text(cr, "▼ " .. fmt_speed(down), 0, 324, 13, P.fg, 1, false, "JetBrains Mono")
  bar(cr, 0, 332, 150, math.min(1, down / 8192), P.accent)
  text(cr, "▲ " .. fmt_speed(up), W, 324, 13, P.fg, 1, false, "JetBrains Mono", "right")
  bar(cr, W - 150, 332, 150, math.min(1, up / 4096), P.accent2)

  -- addresses
  local ip = conky_parse("${addr " .. iface .. "}")
  if ip == nil or ip:match("No Address") or ip == "" then ip = "—" end
  local vpn = conky_parse("${addr tun0}")
  if vpn == nil or vpn:match("No Address") or vpn == "" then vpn = conky_parse("${addr wg0}") end
  local vpn_up = vpn ~= nil and vpn ~= "" and not vpn:match("No Address")
  text(cr, "IP", 0, 372, 12, P.dim, 1, false, "JetBrains Mono")
  text(cr, ip, W, 372, 12, P.fg, 1, false, "JetBrains Mono", "right")
  text(cr, "VPN", 0, 392, 12, P.dim, 1, false, "JetBrains Mono")
  text(cr, vpn_up and vpn or "offline", W, 392, 12, vpn_up and P.ok or P.dim, 1, vpn_up, "JetBrains Mono", "right")
  text(cr, "UPTIME", 0, 412, 12, P.dim, 1, false, "JetBrains Mono")
  text(cr, conky_parse("${uptime_short}"), W, 412, 12, P.fg, 1, false, "JetBrains Mono", "right")

  -- top processes
  color(cr, P.accent, 0.35); cairo_move_to(cr, 0, 436); cairo_line_to(cr, W, 436); cairo_stroke(cr)
  text(cr, "TOP PROCESSES", 0, 456, 11, P.dim, 1, true, "JetBrains Mono")
  for i = 1, 4 do
    local name, c = conky_parse("${top name " .. i .. "}"), num("${top cpu " .. i .. "}")
    text(cr, (name or ""):gsub("%s+", ""), 0, 478 + (i - 1) * 20, 12, P.fg, 0.9, false, "JetBrains Mono")
    text(cr, string.format("%.1f%%", c), W, 478 + (i - 1) * 20, 12, c > 50 and P.accent2 or P.dim, 1, false, "JetBrains Mono", "right")
  end

  cairo_destroy(cr)
  cairo_surface_destroy(cs)
end
