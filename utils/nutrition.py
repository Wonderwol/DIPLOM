def calculate_nutrition(user):
    if not user or not all([user.age, user.weight_kg, user.height_cm, user.goal, user.activity_level, user.gender]):
        return None

    weight = user.weight_kg
    height = user.height_cm
    age = user.age
    gender = user.gender  # исправлено
    goal = user.goal
    activity_level = user.activity_level

    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9
    }

    multiplier = activity_multipliers.get(activity_level, 1.2)
    calories = bmr * multiplier

    if goal == 'похудение':
        calories -= 500
    elif goal == 'набор':
        calories += 300

    protein = weight * 1.8
    fat = weight * 0.9
    protein_kcal = protein * 4
    fat_kcal = fat * 9
    remaining_kcal = calories - (protein_kcal + fat_kcal)
    carbs = remaining_kcal / 4 if remaining_kcal > 0 else 0
    carbs_kcal = carbs * 4

    return {
        'calories': round(calories),
        'protein': round(protein),
        'fat': round(fat),
        'carbs': round(carbs),
        'protein_kcal': round(protein_kcal),
        'fat_kcal': round(fat_kcal),
        'carbs_kcal': round(carbs_kcal)
    }
