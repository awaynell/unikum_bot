img_models = {
    "imagineo": {
        "name": "prithivMLmods/IMAGINEO-4K",
        "params": {
            "negative_prompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
            "use_negative_prompt": True,
            "style": "2560 x 1440",
            "seed": 0,
            "width": 1024,
            "height": 1024,
            "guidance_scale": 6,
            "randomize_seed": True,
            "api_name": "/run"
        }
    },
    "midjourney": {
        "name": "mukaist/Midjourney",
        "params": {
            "negative_prompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
            "use_negative_prompt": True,
            "style": "2560 x 1440",
            "seed": 0,
            "width": 1024,
            "height": 1024,
            "guidance_scale": 6,
            "randomize_seed": True,
            "api_name": "/run"
        }
    },
    "dalle-4k": {
        "name": "mukaist/DALLE-4K",
        "params": {
            "negative_prompt": "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation",
            "use_negative_prompt": True,
            "style": "3840 x 2160",
            "seed": 0,
            "width": 1024,
            "height": 1024,
            "guidance_scale": 6,
            "randomize_seed": True,
            "api_name": "/run"
        }
    },
    "realvisxl": {
        "name": "artificialguybr/RealVisXL-Free-DEMO",
        "params": {
            "negative_prompt": "",
            "seed": 0,
            "custom_width": 1024,
            "custom_height": 1024,
            "guidance_scale": 7,
            "num_inference_steps": 28,
            "sampler": "DPM++ 2M SDE Karras",
            "aspect_ratio_selector": "1024 x 1024",
            "use_upscaler": False,
            "upscaler_strength": 0.55,
            "upscale_by": 1.5,
            "api_name": "/run",
        }
    },
    "gallo-3xl": {
        "name": "prithivMLmods/GALLO-3XL",
        "params": {
            "negative_prompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
            "use_negative_prompt": True,
            "style": "3840 x 2160",
            "seed": 0,
            "width": 1024,
            "height": 1024,
            "guidance_scale": 6,
            "randomize_seed": True,
            "api_name": "/run"
        }
    }
}
