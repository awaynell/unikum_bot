import json

img_providers = {
    "flux": {
        "provider": "Websim",
        "model": "flux"
    },
    "arta_flux": {
        "provider": "ARTA",
        "model": "flux"
    },
    "arta_playground_xl": {
        "provider": "ARTA",
        "model": "playground_xl"
    },
    "arta_playground_xl": {
        "provider": "ARTA",
        "model": "playground_xl"
    },
    "arta_medieval": {
        "provider": "ARTA",
        "model": "medieval"
    },
    "arta_vincent_van_gogh": {
        "provider": "ARTA",
        "model": "vincent_van_gogh"
    },
    "arta_f_dev": {
        "provider": "ARTA",
        "model": "f_dev"
    },
    "arta_low_poly": {
        "provider": "ARTA",
        "model": "low_poly"
    },
    "arta_dreamshaper_xl": {
        "provider": "ARTA",
        "model": "dreamshaper_xl"
    },
    "arta_anima_pencil_xl": {
        "provider": "ARTA",
        "model": "anima_pencil_xl"
    },
    "arta_biomech": {
        "provider": "ARTA",
        "model": "biomech"
    },
    "arta_trash_polka": {
        "provider": "ARTA",
        "model": "trash_polka"
    },
    "arta_no_style": {
        "provider": "ARTA",
        "model": "no_style"
    },
    "arta_cheyenne_xl": {
        "provider": "ARTA",
        "model": "cheyenne_xl"
    },
    "arta_chicano": {
        "provider": "ARTA",
        "model": "chicano"
    },
    "arta_embroidery_tattoo": {
        "provider": "ARTA",
        "model": "embroidery_tattoo"
    },
    "arta_red_and_black": {
        "provider": "ARTA",
        "model": "red_and_black"
    },
    "arta_fantasy_art": {
        "provider": "ARTA",
        "model": "fantasy_art"
    },
    "arta_watercolor": {
        "provider": "ARTA",
        "model": "watercolor"
    },
    "arta_dotwork": {
        "provider": "ARTA",
        "model": "dotwork"
    },
    "arta_old_school_colored": {
        "provider": "ARTA",
        "model": "old_school_colored"
    },
    "arta_realistic_tattoo": {
        "provider": "ARTA",
        "model": "realistic_tattoo"
    },
    "arta_japanese_2": {
        "provider": "ARTA",
        "model": "japanese_2"
    },
    "arta_realistic_stock_xl": {
        "provider": "ARTA",
        "model": "realistic_stock_xl"
    },
    "arta_f_pro": {
        "provider": "ARTA",
        "model": "f_pro"
    },
    "arta_revanimated": {
        "provider": "ARTA",
        "model": "revanimated"
    },
    "arta_katayama_mix_xl": {
        "provider": "ARTA",
        "model": "katayama_mix_xl"
    },
    "arta_sdxl_l": {
        "provider": "ARTA",
        "model": "sdxl_l"
    },
    "arta_cor_epica_xl": {
        "provider": "ARTA",
        "model": "cor_epica_xl"
    },
    "arta_anime_tattoo": {
        "provider": "ARTA",
        "model": "anime_tattoo"
    },
    "arta_new_school": {
        "provider": "ARTA",
        "model": "new_school"
    },
    "arta_death_metal": {
        "provider": "ARTA",
        "model": "death_metal"
    },
    "arta_old_school": {
        "provider": "ARTA",
        "model": "old_school"
    },
    "arta_juggernaut_xl": {
        "provider": "ARTA",
        "model": "juggernaut_xl"
    },
    "arta_photographic": {
        "provider": "ARTA",
        "model": "photographic"
    },
    "arta_sdxl_1_0": {
        "provider": "ARTA",
        "model": "sdxl_1_0"
    },
    "arta_graffiti": {
        "provider": "ARTA",
        "model": "graffiti"
    },
    "arta_mini_tattoo": {
        "provider": "ARTA",
        "model": "mini_tattoo"
    },
    "arta_surrealism": {
        "provider": "ARTA",
        "model": "surrealism"
    },
    "arta_neo_traditional": {
        "provider": "ARTA",
        "model": "neo_traditional"
    },
    "arta_on_limbs_black": {
        "provider": "ARTA",
        "model": "on_limbs_black"
    },
    "arta_yamers_realistic_xl": {
        "provider": "ARTA",
        "model": "yamers_realistic_xl"
    },
    "arta_pony_xl": {
        "provider": "ARTA",
        "model": "pony_xl"
    },
    "arta_playground_xl": {
        "provider": "ARTA",
        "model": "playground_xl"
    },
    "arta_anything_xl": {
        "provider": "ARTA",
        "model": "anything_xl"
    },
    "arta_flame_design": {
        "provider": "ARTA",
        "model": "flame_design"
    },
    "arta_kawaii": {
        "provider": "ARTA",
        "model": "kawaii"
    },
    "arta_cinematic_art": {
        "provider": "ARTA",
        "model": "cinematic_art"
    },
    "arta_professional": {
        "provider": "ARTA",
        "model": "professional"
    },
    "arta_black_ink": {
        "provider": "ARTA",
        "model": "black_ink"
    }
}

max_retry_count = 10
current_retry_count = 0


def reset_retry_count():
    global current_retry_count
    current_retry_count = 0


def increment_retry_count():
    global current_retry_count
    current_retry_count += 1


def load_successful_providers(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
