def bounce(t):
    start_scale = 0.8
    end_scale = 1

    if t >= 0.2:
        return 1

    # Quadratic ease-in function
    progress = t / 0.2
    scale_factor = start_scale + (end_scale - start_scale) * (1 - (1 - progress) ** 2)

    return scale_factor
