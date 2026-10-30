# srn-colors

MATLAB versions of four R color palette packages.

| MATLAB file | Origin (R package) | Palettes |
|---|---|---|
| `matlab/wesanderson.m` | [karthik/wesanderson](https://github.com/karthik/wesanderson) | 24 |
| `matlab/MVZlibrary.m` | [eachambers/MVZlibrary](https://github.com/eachambers/MVZlibrary) | 7 |
| `matlab/NatParksPalettes.m` | [kevinsblake/NatParksPalettes](https://github.com/kevinsblake/NatParksPalettes) | 30 |
| `matlab/poisonfrogs.m` | [laurenoconnelllab/poisonfrogs](https://github.com/laurenoconnelllab/poisonfrogs) | 41 |

All four packages use the MIT license. The license and copyright holder are in the header of each file.

## Use

Add the `matlab` folder to the path. Each function returns an N-by-3 RGB matrix with values from 0 to 1.

```matlab
names = wesanderson("list");                          % list the palettes
set(groot, "defaultAxesColorOrder", wesanderson("Darjeeling1"))
colormap(wesanderson("Zissou1", 256, "continuous"))
rgb = MVZlibrary("theAuk", 5);
rgb = NatParksPalettes("Glacier", [], "discrete", Direction=-1);
```

To look at palettes, call a function with no output:

```matlab
wesanderson                       % figure with all palettes
NatParksPalettes("Arches")        % one palette, with hex codes on the squares
NatParksPalettes("Arches", 256)   % one palette as a 256-step gradient
```

Arguments: `name`, `n`, `type` (`"discrete"` or `"continuous"`).
All four functions accept `Direction=-1`. This reverses the whole palette before the function takes the colors.
`NatParksPalettes` also accepts `OverrideOrder`.

To pick colors at chosen points, use `Index` or `Positions`:

```matlab
wesanderson("Zissou1", Index=[1 3 5])                                % palette colors 1, 3 and 5
wesanderson("Zissou1", Positions=[0 0.25 1])                         % points along the blended palette
NatParksPalettes("Arches", Index=[9 1], Direction=-1)
```

`Index` counts positions in the palette in its source order. `Positions` runs from 0 (first color) to 1 (last color).
Do not combine them with `n`. `Direction` is applied first.
Type `help <function>` for details.

## Demos

Run `demo_wesanderson`, `demo_MVZlibrary`, `demo_NatParksPalettes` or `demo_poisonfrogs` from the `matlab` folder. Each demo shows all palettes, a line plot, and a colormap.

## Adobe swatches

The `swatches` folder has one Adobe Swatch Exchange file for each package:
`wesanderson.ase`, `MVZlibrary.ase`, `NatParksPalettes.ase` and `poisonfrogs.ase`.
Each palette is one color group. The swatches are RGB and follow the palette order in the R source.

To load a file in Illustrator:
1. Open the Swatches panel.
2. Open the panel menu and choose Open Swatch Library, then Other Library.
3. Select an `.ase` file.

## Which palettes to use for which data

Use only these palettes for data that need a perceptual or qualitative scale.
Continuous maps use linear RGB interpolation, so none of them is perfectly perceptually uniform.
For strict quantitative work, use Crameri, cmocean or Colorcet maps.

How the lists were made:
- Sequential and diverging: I computed CIE L* (lightness) along each palette.
  A sequential palette has lightness that rises or falls steadily.
  A diverging palette has one lightness peak in the middle.
  I then removed palettes that pass this test only by chance.
  This test checks lightness only, not hue or gamut.
- Qualitative: the MVZ tag, or the NatParks colorblind flag, from the original authors.
  I did not check them myself.
- `wesanderson` has no tags and no colorblind check.
- `poisonfrogs` has no tags and no colorblind check. Every palette has 5 colors.
  The lightness test passed 33 of the 41 palettes, so it does not separate them well.
  The sequential entries in the table are my choice by eye: smooth dark-to-light ramps.
  There are no diverging palettes. Use the others as discrete (qualitative) palettes only.

| Use | `wesanderson` | `MVZlibrary` | `NatParksPalettes` | `poisonfrogs` |
|---|---|---|---|---|
| Sequential (continuous) | none | Zoology, Ensatina | Arches2, CapitolReef, Glacier, WindCave, Volcanoes, Denali* | Osotokiki*, Rmarina*, Pterribilis*, Oploma* |
| Diverging (continuous) | Zissou1 | LifeHistories, theAuk | Acadia, Arches, Olympic* | none |
| Qualitative (discrete) | all others | NaturalHistory, FieldNotes, WesternBirds | Cuyahoga, DeathValley, Halekala, KingsCanyon, Triglav (colorblind flagged) | all others* |

\* Not flagged colorblind friendly by the authors. Check before you use it.

Use the discrete (qualitative) palettes with a small `n`. They have no ordered lightness, so do not use them as colormaps.

## Differences from the R packages

- `MVZlibrary`: for a discrete request with n smaller than the palette, R keeps the n colors nearest to the first color. MATLAB keeps n evenly spaced colors.
- Continuous palettes use linear RGB interpolation, as `colorRampPalette` does in R.
- `poisonfrogs`: the R package blends colors with a spline (`splinefun`, method "fmm"). MATLAB uses its own `spline` method (not-a-knot). Both are cubic splines, but the blended colors can differ slightly. Values are clipped to the range 0 to 1.
- `poisonfrogs`: with no `n`, a continuous request gives 256 colors, as in R.

## Regenerate the MATLAB files

Do not edit the `.m` files by hand. Clone the four R repos. Then run:

```
python tools/generate_palettes.py WES_DIR MVZ_DIR NAT_DIR POISON_DIR matlab
```

This also rewrites the `.ase` files in the `swatches` folder.


## AI-generated code

I had an ai Agent generate pretty much all of this code (claude specifically). For a personal project like this, which is largely just using other repos of colors in MATLAB instead of R, I don't feel very strongly one way or the other about AI generated code, and I suspect that the outputs are largely good enough, particularly since all outputs can be checked by eye. If your application is truly sensitive to colormap perceptuality, like medical image analysis or diagnosis, don't use this repo, use something more established/correct please. If you have a problem with this, you can complain about it to your own AI agent :).
