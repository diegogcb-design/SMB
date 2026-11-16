# Pixel Platformer Tileset (Free)
by reodesuxz

106 hand-built 16x16 pixel art sprites for 2D platformers: 4 terrain sets with auto-tile pieces, blocks, hazards, items, props, characters and a parallax-ready background.

## Contents
- tileset_16x16.png      - all 16x16 tiles on one sheet (16 columns, no spacing) - ready for Tiled, Godot TileMap, Unity Tile Palette, GameMaker
- tileset_16x16_x4.png   - the same sheet scaled 4x
- props_sheet.png        - larger props (tree 32x48, pine 32x48, bush 32x16, cloud 32x16, flag 16x32, door 16x32)
- sprite_index.json      - name and pixel rectangle of every sprite on the sheets
- sprites_1x/            - every sprite as its own PNG (original size)
- sprites_4x/            - every sprite as its own PNG scaled 4x (nearest neighbour)
- background_320x180.png / background_1280x720.png - sky and hills background

## Sprites
- Terrain (52): grass_tl, grass_t, grass_tr, grass_l, grass_m, grass_r, grass_bl, grass_b, grass_br, grass_single, grass_strip_l, grass_strip_m, grass_strip_r, stone_tl, stone_t, stone_tr, stone_l, stone_m, stone_r, stone_bl, stone_b, stone_br, stone_single, stone_strip_l, stone_strip_m, stone_strip_r, sand_tl, sand_t, sand_tr, sand_l, sand_m, sand_r, sand_bl, sand_b, sand_br, sand_single, sand_strip_l, sand_strip_m, sand_strip_r, snow_tl, snow_t, snow_tr, snow_l, snow_m, snow_r, snow_bl, snow_b, snow_br, snow_single, snow_strip_l, snow_strip_m, snow_strip_r
- Blocks (8): bricks, stone_bricks, wood_planks, crate, metal_block, question_block, question_block_used, ice_block
- Platforms (4): wood_platform_l, wood_platform_m, wood_platform_r, ladder
- Hazards (5): spikes, water_top, water, lava_top, lava
- Items (13): coin_0, coin_1, coin_2, coin_3, gem_blue, gem_red, gem_green, heart, heart_empty, key, potion_red, potion_blue, star
- Props (16): bush, tree, pine_tree, cloud, rock, flowers_red, flowers_blue, grass_tuft, mushroom, fence, sign, goal_flag, door, torch, chest, chest_open
- Characters (8): slime_green_0, slime_blue_0, slime_green_1, slime_blue_1, bat_0, bat_1, hero_idle, hero_run

Terrain naming: tl/t/tr/l/m/r/bl/b/br = 9-slice pieces, single = one-tile block, strip_l/m/r = one-tile-high floating platform.
Animations: coin_0-3 (spin), slime_*_0-1 (bounce), bat_0-1 (flap), hero_idle / hero_run.

## Tips
- Import with filtering OFF (Point / Nearest) so pixels stay sharp.
- 16 colour palette based on Sweetie 16, so everything matches.

## License
See LICENSE.txt. Free to use in unlimited personal and commercial projects. You may not resell or redistribute the sprites themselves.
If this pack helped you, a small tip on itch.io keeps more free packs coming. Thank you!
