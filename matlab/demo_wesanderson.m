%% demo_wesanderson  Swatches and example plots for wesanderson.m
% Run this script from the folder that holds wesanderson.m.
% Part 1: swatches of all palettes.
% Part 2: a palette as the line color order.
% Part 3: a palette as a continuous colormap.
clear; close all
pkg   = @wesanderson;
names = pkg("list");
catName  = "Darjeeling1";    % palette for the line plot
contName = "Zissou1";   % palette for the colormap

%% 1. All palettes
fig = figure("Name", "wesanderson swatches", "Color", "w");
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
title(ax, "wesanderson", "Interpreter", "none")

%% 2. Palette as line colors
c5 = pkg(catName, 5);
fig = figure("Name", "wesanderson lines", "Color", "w");
ax = axes(fig); hold(ax, "on")
ax.ColorOrder = c5;
x = linspace(0, 2*pi, 200);
for k = 1:size(c5, 1)
    plot(ax, x, sin(x + k/2), "LineWidth", 2)
end
legend(ax, "Location", "southwest", "Box", "off"); box(ax, "off")
title(ax, catName + " (n = 5)", "Interpreter", "none")

%% 3. Palette as colormap
fig = figure("Name", "wesanderson colormap", "Color", "w");
ax = axes(fig);
imagesc(ax, peaks(200)); axis(ax, "image")
colormap(ax, pkg(contName, 256, "continuous")); colorbar(ax)
title(ax, contName + " (continuous)", "Interpreter", "none")
