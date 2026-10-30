"""Generate MATLAB palette functions and demo scripts from the R palette repos.

Usage:
    python generate_palettes.py WES_DIR MVZ_DIR NAT_DIR POISON_DIR OUT_DIR [SWATCH_DIR]

WES_DIR, MVZ_DIR, NAT_DIR and POISON_DIR are local clones of
    https://github.com/karthik/wesanderson
    https://github.com/eachambers/MVZlibrary
    https://github.com/kevinsblake/NatParksPalettes
    https://github.com/laurenoconnelllab/poisonfrogs
OUT_DIR receives wesanderson.m, MVZlibrary.m, NatParksPalettes.m, poisonfrogs.m and one
demo_<name>.m script for each of them. SWATCH_DIR (default: ../swatches next
to OUT_DIR) receives one Adobe Swatch Exchange file (.ase) per package, with
one color group per palette.
"""
from __future__ import annotations

import re
import struct
import subprocess
import sys
from pathlib import Path

HEX = re.compile(r'"(#[0-9A-Fa-f]{6})"')
WES_LINE = re.compile(r'^\s*(\w+)\s*=\s*c\(([^)]*)\)')
MVZ_LINE = re.compile(r'^\s*(\w+)\s*=\s*list\(c\(([^)]*)\),\s*type\s*=\s*"(\w+)"\)')
NAT_LINE = re.compile(
    r'^\s*(\w+)\s*=\s*list\(c\(([^)]*)\),\s*c\(([^)]*)\),\s*colorblind\s*=\s*(TRUE|FALSE)\)'
)


def hexes(text: str) -> list[str]:
    return [h.upper() for h in HEX.findall(text)]


def mat_hex(colors: list[str]) -> str:
    return "[" + " ".join(f'"{c}"' for c in colors) + "]"


def commit(repo: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return out.stdout.strip() or "unknown"


def code_lines(path: Path) -> list[str]:
    return [ln for ln in path.read_text(encoding="utf-8").splitlines()
            if not ln.lstrip().startswith("#")]


def parse_wes(repo: Path) -> dict:
    pals = {}
    for ln in code_lines(repo / "R" / "colors.R"):
        m = WES_LINE.match(ln)
        if m and HEX.search(m.group(2)):
            pals[m.group(1)] = hexes(m.group(2))
    return pals


def parse_poison(repo: Path) -> dict:
    pals = {}
    for ln in code_lines(repo / "R" / "poison_frog_palettes.R"):
        m = WES_LINE.match(ln)
        if m and HEX.search(m.group(2)):
            pals[m.group(1)] = hexes(m.group(2))
    return pals


def parse_mvz(repo: Path) -> dict:
    pals = {}
    for ln in code_lines(repo / "R" / "MVZlibrary_palettes.R"):
        m = MVZ_LINE.match(ln)
        if m:
            pals[m.group(1)] = (hexes(m.group(2)), m.group(3))
    return pals


def parse_nat(repo: Path) -> dict:
    pals = {}
    for ln in code_lines(repo / "R" / "NatParksPalettes.R"):
        m = NAT_LINE.match(ln)
        if m:
            order = [int(x) for x in m.group(3).split(",")]
            pals[m.group(1)] = (hexes(m.group(2)), order, m.group(4) == "TRUE")
    return pals


def ase_bytes(palettes: dict[str, list[str]]) -> bytes:
    """Adobe Swatch Exchange file: one group per palette, RGB global colors."""
    def name(text: str) -> bytes:
        return struct.pack(">H", len(text) + 1) + (text + "\0").encode("utf-16-be")

    def block(kind: int, body: bytes) -> bytes:
        return struct.pack(">HI", kind, len(body)) + body

    blocks = []
    for pal, colors in palettes.items():
        blocks.append(block(0xC001, name(pal)))
        for c in colors:
            rgb = [int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            body = name(f"{pal} {c}") + b"RGB " + struct.pack(">3fH", *rgb, 0)
            blocks.append(block(0x0001, body))
        blocks.append(block(0xC002, b""))
    return b"ASEF" + struct.pack(">HHI", 1, 0, len(blocks)) + b"".join(blocks)


# --------------------------------------------------------------------------
# Shared MATLAB helper code (local functions appended to every generated file)
# --------------------------------------------------------------------------
HELPERS = r'''
function rgb = hex2rgb_(hex)
% Convert a string array of "#RRGGBB" codes to an N-by-3 matrix in [0,1].
h = char(extractAfter(hex(:), "#"));
rgb = [hex2dec(h(:,1:2)), hex2dec(h(:,3:4)), hex2dec(h(:,5:6))] / 255;
end

function rgb = ramp_(base, n, method)
% Interpolation in RGB between the palette colors. The default is linear,
% the same as R's colorRampPalette.
if nargin < 3
    method = "linear";
end
if n == 1
    rgb = base(1,:);
    return
end
x = linspace(0, 1, size(base,1));
rgb = min(max(interp1(x, base, linspace(0, 1, n), method), 0), 1);
end

function show_swatches_(label, names, colors)
% Draw palettes as rows of colored squares, one row for each palette.
% A single palette also gets its hex codes written on the squares.
names = string(names);
nRows = numel(names);
single = nRows == 1;
fig = figure("Name", label, "Color", "w", "NumberTitle", "off");
if single
    fig.Position(3:4) = [620, 140];
else
    fig.Position(3:4) = [560, 40 + 22 * nRows];
end
ax = axes(fig); hold(ax, "on")
for i = 1:nRows
    c = colors{i};
    m = size(c, 1);
    w = min(1, 10 / m);
    for j = 1:m
        rectangle(ax, "Position", [(j - 1) * w, -i, w, 0.9], ...
            "FaceColor", c(j,:), "EdgeColor", "none");
        if single && m <= 12
            lum = [0.2126 0.7152 0.0722] * c(j,:)';
            text(ax, (j - 0.5) * w, -i + 0.45, sprintf("#%02X%02X%02X", round(c(j,:) * 255)), ...
                "HorizontalAlignment", "center", "FontSize", 8, "Color", [1 1 1] * (lum < 0.5))
        end
    end
end
set(ax, "YTick", (-nRows:-1) + 0.45, "YTickLabel", flip(names), ...
    "XTick", [], "TickLabelInterpreter", "none", "TickLength", [0 0], "Box", "off")
axis(ax, "tight"); ax.YAxis.Color = "none"; ax.YAxis.TickLabelColor = "k";
title(ax, label, "Interpreter", "none")
end

function rgb = pick_(base, n, index, positions, method)
% Colors at chosen palette positions (index), or at fractions from 0 to 1
% along the blended palette (positions).
if nargin < 5
    method = "linear";
end
if ~isempty(n)
    error("palette:conflictingOptions", "Do not combine n with Index or Positions.")
end
if ~isempty(index) && ~isempty(positions)
    error("palette:conflictingOptions", "Use Index or Positions, not both.")
end
if ~isempty(index)
    if any(index > size(base, 1))
        error("palette:badIndex", "Index must be between 1 and %d.", size(base, 1))
    end
    rgb = base(index(:), :);
else
    x = linspace(0, 1, size(base, 1));
    rgb = min(max(interp1(x, base, positions(:), method), 0), 1);
end
end
'''

WES_TEMPLATE = r'''function [rgb, info] = wesanderson(name, n, type, opts)
%WESANDERSON  Wes Anderson color palettes.
%   rgb = wesanderson(name)                  all colors of a palette (N-by-3)
%   rgb = wesanderson(name, n)               first n colors
%   rgb = wesanderson(name, n, "continuous") n colors interpolated in RGB
%   names = wesanderson("list")              names of all palettes
%   wesanderson                              show all palettes in a figure
%   wesanderson(name, ...)                   with no output: show that palette
%
%   Option (name-value)
%       Direction  1 (default) or -1. With -1 the whole palette is reversed
%                  first, then the colors are taken (so n = 3 gives the last
%                  3 colors of the palette, in reverse order).
%       Index      Pick colors by position in the palette, in the order you
%                  give, for example Index=[1 3 5]. Repeats are allowed.
%                  Do not combine with n.
%       Positions  Pick colors at fractions from 0 (first color) to 1 (last
%                  color) along the blended palette, for example
%                  Positions=[0 0.25 1]. Do not combine with n or Index.
%

%   "Zissou1" with type "continuous" uses the hand-made "Zissou1Continuous"
%   palette, as the R package does.
%
%   Example
%       set(groot, "defaultAxesColorOrder", wesanderson("Darjeeling1"))
%       colormap(wesanderson("Zissou1", 256, "continuous"))
%
%   Source:  https://github.com/karthik/wesanderson  (commit __COMMIT__)
%   License: MIT, Copyright (c) 2022 Karthik Ram
%   Generated by tools/generate_palettes.py. Do not edit by hand.
arguments
    name (1,1) string = ""
    n double {mustBeInteger, mustBePositive, mustBeScalarOrEmpty} = []
    type (1,1) string {mustBeMember(type, ["discrete", "continuous"])} = "discrete"
    opts.Direction (1,1) double {mustBeMember(opts.Direction, [1 -1])} = 1
    opts.Index double {mustBeInteger, mustBePositive} = []
    opts.Positions double {mustBeGreaterThanOrEqual(opts.Positions, 0), mustBeLessThanOrEqual(opts.Positions, 1)} = []
end
P = palettes_();
info = [];
if name == "" || name == "list"
    names = string(fieldnames(P));
    if name == "" && nargout == 0
        show_swatches_("wesanderson", names, arrayfun(@(k) wesanderson(k), names, "UniformOutput", false))
        return
    end
    rgb = names;
    return
end
if ~isfield(P, name)
    error("wesanderson:unknownPalette", "Palette ""%s"" not found. Use wesanderson(""list"").", name)
end
hex = P.(name);
if type == "continuous" && name == "Zissou1"
    hex = P.Zissou1Continuous;
end
base = hex2rgb_(hex);
if opts.Direction == -1
    base = flipud(base);
end
if ~isempty(opts.Index) || ~isempty(opts.Positions)
    rgb = pick_(base, n, opts.Index, opts.Positions);
    if nargout == 0
        show_swatches_(name, name, {rgb})
        clear rgb info
    end
    return
end
if isempty(n)
    n = size(base, 1);
end
if type == "discrete"
    if n > size(base, 1)
        error("wesanderson:tooManyColors", ...
            "Palette ""%s"" has %d colors. Use type ""continuous"" for more.", name, size(base, 1))
    end
    rgb = base(1:n, :);
else
    rgb = ramp_(base, n);
end
if nargout == 0
    show_swatches_(name, name, {rgb})
    clear rgb info
end
end

function P = palettes_()
__DATA__
end
''' + HELPERS

POISON_TEMPLATE = r'''function [rgb, info] = poisonfrogs(name, n, type, opts)
%POISONFROGS  Color palettes inspired by poison frogs and other frogs.
%   rgb = poisonfrogs(name)                  all 5 colors of a palette (5-by-3)
%   rgb = poisonfrogs(name, n)               first n colors
%   rgb = poisonfrogs(name, n, "continuous") n colors interpolated with a spline
%   names = poisonfrogs("list")              names of all palettes
%   poisonfrogs                              show all palettes in a figure
%   poisonfrogs(name, ...)                   with no output: show that palette
%
%   Option (name-value)
%       Direction  1 (default) or -1. With -1 the whole palette is reversed
%                  first, then the colors are taken (so n = 3 gives the last
%                  3 colors of the palette, in reverse order).
%       Index      Pick colors by position in the palette, in the order you
%                  give, for example Index=[1 3 5]. Repeats are allowed.
%                  Do not combine with n.
%       Positions  Pick colors at fractions from 0 (first color) to 1 (last
%                  color) along the blended palette, for example
%                  Positions=[0 0.25 1]. Do not combine with n or Index.
%
%   Difference from the R package: the R package blends colors with
%   splinefun (method "fmm"). This version uses the MATLAB "spline" method
%   (not-a-knot). Both are cubic splines. The blended colors can differ
%   slightly. Values are clipped to the range 0 to 1, as in R.
%
%   Example
%       set(groot, "defaultAxesColorOrder", poisonfrogs("Ramazonica"))
%       colormap(poisonfrogs("Osotokiki", 256, "continuous"))
%
%   Source:  https://github.com/laurenoconnelllab/poisonfrogs  (commit __COMMIT__)
%   License: MIT, Copyright (c) 2025 Camilo Rodriguez Lopez
%   Generated by tools/generate_palettes.py. Do not edit by hand.
arguments
    name (1,1) string = ""
    n double {mustBeInteger, mustBePositive, mustBeScalarOrEmpty} = []
    type (1,1) string {mustBeMember(type, ["discrete", "continuous"])} = "discrete"
    opts.Direction (1,1) double {mustBeMember(opts.Direction, [1 -1])} = 1
    opts.Index double {mustBeInteger, mustBePositive} = []
    opts.Positions double {mustBeGreaterThanOrEqual(opts.Positions, 0), mustBeLessThanOrEqual(opts.Positions, 1)} = []
end
P = palettes_();
info = [];
if name == "" || name == "list"
    names = string(fieldnames(P));
    if name == "" && nargout == 0
        show_swatches_("poisonfrogs", names, arrayfun(@(k) poisonfrogs(k), names, "UniformOutput", false))
        return
    end
    rgb = names;
    return
end
if ~isfield(P, name)
    error("poisonfrogs:unknownPalette", "Palette ""%s"" not found. Use poisonfrogs(""list"").", name)
end
base = hex2rgb_(P.(name));
if opts.Direction == -1
    base = flipud(base);
end
if ~isempty(opts.Index) || ~isempty(opts.Positions)
    rgb = pick_(base, n, opts.Index, opts.Positions, "spline");
    if nargout == 0
        show_swatches_(name, name, {rgb})
        clear rgb info
    end
    return
end
if isempty(n)
    if type == "discrete"
        n = size(base, 1);
    else
        n = 256;
    end
end
if type == "discrete"
    if n > size(base, 1)
        error("poisonfrogs:tooManyColors", ...
            "Palette ""%s"" has %d colors. Use type ""continuous"" for more.", name, size(base, 1))
    end
    rgb = base(1:n, :);
else
    rgb = ramp_(base, n, "spline");
end
if nargout == 0
    show_swatches_(name, name, {rgb})
    clear rgb info
end
end

function P = palettes_()
__DATA__
end
''' + HELPERS

MVZ_TEMPLATE = r'''function [rgb, info] = MVZlibrary(name, n, type, opts)
%MVZLIBRARY  Color palettes from the MVZ library (UC Berkeley).
%   rgb = MVZlibrary(name)                  all colors of a palette (N-by-3)
%   rgb = MVZlibrary(name, n)               n colors, evenly spread over the palette
%   rgb = MVZlibrary(name, n, "continuous") n colors interpolated in RGB
%   [names, types] = MVZlibrary("list")     palette names and their type
%   MVZlibrary                              show all palettes in a figure
%   MVZlibrary(name, ...)                   with no output: show that palette
%
%   Option (name-value)
%       Direction  1 (default) or -1. With -1 the whole palette is reversed
%                  first, then the colors are taken.
%       Index      Pick colors by position in the palette, in the order you
%                  give, for example Index=[1 3 5]. Repeats are allowed.
%                  Do not combine with n.
%       Positions  Pick colors at fractions from 0 (first color) to 1 (last
%                  color) along the blended palette, for example
%                  Positions=[0 0.25 1]. Do not combine with n or Index.
%   [rgb, info] = MVZlibrary(name, ...)     info is "qualitative", "diverging"
%                                           or "monochromatic"
%
%   Difference from the R package: for a discrete request with n smaller than
%   the palette length, R keeps the n colors closest to the first color
%   (colorblindcheck::palette_dist). This version keeps n evenly spaced colors
%   instead, so the choice does not depend on the first color.
%
%   Example
%       set(groot, "defaultAxesColorOrder", MVZlibrary("FieldNotes"))
%       colormap(MVZlibrary("theAuk", 256, "continuous"))
%
%   Source:  https://github.com/eachambers/MVZlibrary  (commit __COMMIT__)
%   License: MIT, Copyright (c) 2023 E. Anne Chambers
%   Generated by tools/generate_palettes.py. Do not edit by hand.
arguments
    name (1,1) string = ""
    n double {mustBeInteger, mustBePositive, mustBeScalarOrEmpty} = []
    type (1,1) string {mustBeMember(type, ["discrete", "continuous"])} = "discrete"
    opts.Direction (1,1) double {mustBeMember(opts.Direction, [1 -1])} = 1
    opts.Index double {mustBeInteger, mustBePositive} = []
    opts.Positions double {mustBeGreaterThanOrEqual(opts.Positions, 0), mustBeLessThanOrEqual(opts.Positions, 1)} = []
end
P = palettes_();
if name == "" || name == "list"
    names = string(fieldnames(P));
    if name == "" && nargout == 0
        show_swatches_("MVZlibrary", names, arrayfun(@(k) MVZlibrary(k), names, "UniformOutput", false))
        return
    end
    rgb = names;
    info = arrayfun(@(f) string(P.(f{1}).type), fieldnames(P));
    return
end
if ~isfield(P, name)
    error("MVZlibrary:unknownPalette", "Palette ""%s"" not found. Use MVZlibrary(""list"").", name)
end
base = hex2rgb_(P.(name).hex);
if opts.Direction == -1
    base = flipud(base);
end
if ~isempty(opts.Index) || ~isempty(opts.Positions)
    rgb = pick_(base, n, opts.Index, opts.Positions);
    if nargout == 0
        show_swatches_(name, name, {rgb})
        clear rgb info
    end
    return
end
info = string(P.(name).type);
if isempty(n)
    n = size(base, 1);
end
if type == "discrete"
    if n > size(base, 1)
        error("MVZlibrary:tooManyColors", ...
            "Palette ""%s"" has %d colors. Use type ""continuous"" for more.", name, size(base, 1))
    end
    rgb = base(round(linspace(1, size(base, 1), n)), :);
else
    rgb = ramp_(base, n);
end
if nargout == 0
    show_swatches_(name, name, {rgb})
    clear rgb info
end
end

function P = palettes_()
__DATA__
end
''' + HELPERS

NAT_TEMPLATE = r'''function [rgb, info] = NatParksPalettes(name, n, type, opts)
%NATPARKSPALETTES  Color palettes inspired by US and world national parks.
%   rgb = NatParksPalettes(name)                  all colors of a palette (N-by-3)
%   rgb = NatParksPalettes(name, n)               n colors, picked in the order that
%                                                 the authors chose for readability
%   rgb = NatParksPalettes(name, n, "continuous") n colors interpolated in RGB
%   [names, cb] = NatParksPalettes("list")        palette names and colorblind flags
%   NatParksPalettes                              show all palettes in a figure
%   NatParksPalettes(name, ...)                   with no output: show that palette
%   [rgb, cb] = NatParksPalettes(name, ...)       cb is true if the palette is
%                                                 colorblind friendly
%
%   Options (name-value, as in the R package)
%       Direction     1 (default) or -1 to reverse the colors
%       OverrideOrder true to take the first n colors instead of the
%                     authors' readability order (discrete only)
%       Index         Pick colors by position in the palette (source order,
%                     not readability order), for example Index=[1 3 5].
%                     Repeats are allowed. Do not combine with n.
%       Positions     Pick colors at fractions from 0 (first color) to 1
%                     (last color) along the blended palette, for example
%                     Positions=[0 0.25 1]. Do not combine with n or Index.
%                     Direction applies to both.
%
%   Direction = -1 with discrete colors:
%       OverrideOrder false: pick the n colors by readability order, then
%                            reverse those n colors.
%       OverrideOrder true:  reverse the whole palette, then take the first
%                            n colors (the last n colors of the original).
%
%   If type is not given, it is "continuous" when n is larger than the
%   palette, and "discrete" otherwise.
%
%   Example
%       set(groot, "defaultAxesColorOrder", NatParksPalettes("Yellowstone"))
%       colormap(NatParksPalettes("Arches", 256, "continuous"))
%       NatParksPalettes("Glacier", [], "discrete", Direction=-1)
%
%   Source:  https://github.com/kevinsblake/NatParksPalettes  (commit __COMMIT__)
%   License: MIT, Copyright (c) 2022 Kevin S. Blake
%   Generated by tools/generate_palettes.py. Do not edit by hand.
arguments
    name (1,1) string = ""
    n double {mustBeInteger, mustBePositive, mustBeScalarOrEmpty} = []
    type (1,1) string {mustBeMember(type, ["auto", "discrete", "continuous"])} = "auto"
    opts.Direction (1,1) double {mustBeMember(opts.Direction, [1 -1])} = 1
    opts.Index double {mustBeInteger, mustBePositive} = []
    opts.Positions double {mustBeGreaterThanOrEqual(opts.Positions, 0), mustBeLessThanOrEqual(opts.Positions, 1)} = []
    opts.OverrideOrder (1,1) logical = false
end
P = palettes_();
if name == "" || name == "list"
    names = string(fieldnames(P));
    if name == "" && nargout == 0
        show_swatches_("NatParksPalettes", names, arrayfun(@(k) NatParksPalettes(k), names, "UniformOutput", false))
        return
    end
    rgb = names;
    info = arrayfun(@(f) P.(f{1}).colorblind, fieldnames(P));
    return
end
if ~isfield(P, name)
    error("NatParksPalettes:unknownPalette", "Palette ""%s"" not found. Use NatParksPalettes(""list"").", name)
end
p = P.(name);
info = p.colorblind;
base = hex2rgb_(p.hex);
if ~isempty(opts.Index) || ~isempty(opts.Positions)
    if opts.Direction == -1
        base = flipud(base);
    end
    rgb = pick_(base, n, opts.Index, opts.Positions);
    if nargout == 0
        show_swatches_(name, name, {rgb})
        clear rgb info
    end
    return
end
if isempty(n)
    n = size(base, 1);
end
if type == "auto"
    if n > size(base, 1)
        type = "continuous";
    else
        type = "discrete";
    end
end
if type == "discrete"
    if n > size(base, 1)
        error("NatParksPalettes:tooManyColors", ...
            "Palette ""%s"" has %d colors. Use type ""continuous"" for more.", name, size(base, 1))
    end
    if opts.OverrideOrder
        if opts.Direction == -1
            base = flipud(base);
        end
        rgb = base(1:n, :);
    else
        rgb = base(p.order <= n, :);
        if opts.Direction == -1
            rgb = flipud(rgb);
        end
    end
else
    if opts.Direction == -1
        base = flipud(base);
    end
    rgb = ramp_(base, n);
end
if nargout == 0
    show_swatches_(name, name, {rgb})
    clear rgb info
end
end

function P = palettes_()
__DATA__
end
''' + HELPERS

DEMO_TEMPLATE = r'''%% demo___PKG__  Swatches and example plots for __PKG__.m
% Run this script from the folder that holds __PKG__.m.
% Part 1: swatches of all palettes.
% Part 2: a palette as the line color order.
% Part 3: a palette as a continuous colormap.
clear; close all
pkg   = @__PKG__;
names = pkg("list");
catName  = "__CAT__";    % palette for the line plot
contName = "__CONT__";   % palette for the colormap

%% 1. All palettes
fig = figure("Name", "__PKG__ swatches", "Color", "w");
fig.Position(3:4) = [560, 40 + 22 * numel(names)];
ax = axes(fig); hold(ax, "on")
for i = 1:numel(names)
    c = pkg(names(i));
    for j = 1:size(c, 1)
        rectangle(ax, "Position", [j - 1, -i, 1, 0.9], ...
            "FaceColor", c(j,:), "EdgeColor", "none");
    end
end
set(ax, "YTick", (-numel(names):-1) + 0.45, "YTickLabel", flip(names), ...
    "XTick", [], "TickLabelInterpreter", "none", "TickLength", [0 0], "Box", "off")
axis(ax, "tight"); ax.YAxis.Color = "none"; ax.YAxis.TickLabelColor = "k";
title(ax, "__PKG__", "Interpreter", "none")

%% 2. Palette as line colors
c5 = pkg(catName, 5);
fig = figure("Name", "__PKG__ lines", "Color", "w");
ax = axes(fig); hold(ax, "on")
ax.ColorOrder = c5;
x = linspace(0, 2*pi, 200);
for k = 1:size(c5, 1)
    plot(ax, x, sin(x + k/2), "LineWidth", 2)
end
legend(ax, "Location", "southwest", "Box", "off"); box(ax, "off")
title(ax, catName + " (n = 5)", "Interpreter", "none")

%% 3. Palette as colormap
fig = figure("Name", "__PKG__ colormap", "Color", "w");
ax = axes(fig);
imagesc(ax, peaks(200)); axis(ax, "image")
colormap(ax, pkg(contName, 256, "continuous")); colorbar(ax)
title(ax, contName + " (continuous)", "Interpreter", "none")
'''


def main(argv: list[str]) -> None:
    if len(argv) not in (6, 7):
        sys.exit(__doc__)
    wes_dir, mvz_dir, nat_dir, poison_dir, out = (Path(a) for a in argv[1:6])
    swatches = Path(argv[6]) if len(argv) == 7 else out.parent / "swatches"
    out.mkdir(parents=True, exist_ok=True)
    swatches.mkdir(parents=True, exist_ok=True)

    wes = parse_wes(wes_dir)
    mvz = parse_mvz(mvz_dir)
    nat = parse_nat(nat_dir)
    poison = parse_poison(poison_dir)
    print(f"parsed: wesanderson={len(wes)}  MVZlibrary={len(mvz)}  "
          f"NatParksPalettes={len(nat)}  poisonfrogs={len(poison)}")

    wes_data = "\n".join(f'P.{k} = {mat_hex(v)};' for k, v in wes.items())
    poison_data = "\n".join(f'P.{k} = {mat_hex(v)};' for k, v in poison.items())
    mvz_data = "\n".join(
        f'P.{k} = struct("hex", {mat_hex(h)}, "type", "{t}");' for k, (h, t) in mvz.items()
    )
    nat_data = "\n".join(
        f'P.{k} = struct("hex", {mat_hex(h)}, "order", [{" ".join(map(str, o))}], '
        f'"colorblind", {str(cb).lower()});'
        for k, (h, o, cb) in nat.items()
    )

    jobs = [
        ("wesanderson", WES_TEMPLATE, wes_data, wes_dir, "Darjeeling1", "Zissou1", wes),
        ("MVZlibrary", MVZ_TEMPLATE, mvz_data, mvz_dir, "FieldNotes", "theAuk",
         {k: v[0] for k, v in mvz.items()}),
        ("NatParksPalettes", NAT_TEMPLATE, nat_data, nat_dir, "Yellowstone", "Arches",
         {k: v[0] for k, v in nat.items()}),
        ("poisonfrogs", POISON_TEMPLATE, poison_data, poison_dir, "Ramazonica", "Osotokiki",
         poison),
    ]
    for pkg, template, data, repo, cat, cont, hex_by_name in jobs:
        data = "\n".join("    " + ln for ln in data.splitlines())
        text = template.replace("__COMMIT__", commit(repo)).replace("__DATA__", data)
        (out / f"{pkg}.m").write_text(text, encoding="utf-8", newline="\n")
        demo = (DEMO_TEMPLATE.replace("__PKG__", pkg)
                .replace("__CAT__", cat).replace("__CONT__", cont))
        (out / f"demo_{pkg}.m").write_text(demo, encoding="utf-8", newline="\n")
        (swatches / f"{pkg}.ase").write_bytes(ase_bytes(hex_by_name))
        print(f"wrote {pkg}.m, demo_{pkg}.m and {pkg}.ase")


if __name__ == "__main__":
    main(sys.argv)
