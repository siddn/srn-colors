%% demo_MVZlibrary  Swatches and example plots for MVZlibrary.m
% Run this script from the folder that holds MVZlibrary.m.
% Part 1: swatches of all palettes.
% Part 2: a palette as the line color order.
% Part 3: a palette as a continuous colormap.
clear; close all
pkg   = @MVZlibrary;
names = pkg("list");
catName  = "FieldNotes";    % palette for the line plot
contName = "theAuk";   % palette for the colormap

%% 1. All palettes
fig = figure("Name", "MVZlibrary swatches", "Color", "w");
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
title(ax, "MVZlibrary", "Interpreter", "none")

%% 2. Palette as line colors
c5 = pkg(catName, 5);
fig = figure("Name", "MVZlibrary lines", "Color", "w");
ax = axes(fig); hold(ax, "on")
ax.ColorOrder = c5;
x = linspace(0, 2*pi, 200);
for k = 1:size(c5, 1)
    plot(ax, x, sin(x + k/2), "LineWidth", 2)
end
legend(ax, "Location", "southwest", "Box", "off"); box(ax, "off")
title(ax, catName + " (n = 5)", "Interpreter", "none")

%% 3. Palette as colormap
fig = figure("Name", "MVZlibrary colormap", "Color", "w");
ax = axes(fig);
imagesc(ax, peaks(200)); axis(ax, "image")
colormap(ax, pkg(contName, 256, "continuous")); colorbar(ax)
title(ax, contName + " (continuous)", "Interpreter", "none")
