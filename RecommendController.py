import os
import pickle
from pathlib import Path
import pandas as pd
import numpy as np


stored_folder = Path(os.path.abspath('')) / "data" / "processed" / "cleaned_df.pkl"
recipe = pickle.load(open(stored_folder, 'rb'))


stored_folder = Path(os.path.abspath('')) / "data" / "model" / "recommend_model.pkl"
model = pickle.load(open(stored_folder, 'rb'))


def merge_data(recipe_df, user_df):
    merged_df = recipe_df.merge(user_df, left_on="RecipeId", right_on="recipe_id")
    return merged_df


def get_category_list(merged_df):
    category_unique_values = merged_df['RecipeCategory'].dropna().unique().tolist()
    return category_unique_values


def make_category(df, category_list):
    d = {name: [] for name in category_list}

    def f(row):
        categories = str(row['RecipeCategory'])
        for category in category_list:
            if category in categories:
                d[category].append(1)
            else:
                d[category].append(0)

    df.apply(f, axis=1)
    category_df = pd.DataFrame(d, columns=category_list)
    df = pd.concat([df, category_df], axis=1)
    return df


class RecommendController:

    @staticmethod
    def make_user_feature(df):
        df = pd.DataFrame(df)
        df['rating_count'] = df.groupby('user_id')['recipe_id'].transform('count')
        df['rating_mean'] = df.groupby('user_id')['rating'].transform('mean')
        return df

    @staticmethod
    def predict(user_df, top_k):
        user_recipe_df = recipe.merge(user_df, left_on="AuthorId", right_on="author_id")
        category_unique_values = recipe['RecipeCategory'].dropna().unique().tolist()
        user_recipe_df = make_category(user_recipe_df, category_unique_values)
        excludes_category = list(np.array(category_unique_values)[np.nonzero([user_recipe_df[category_unique_values].sum(axis=0) < 1])[1]])

        features = ['AggregatedRating', 'ReviewCount', 'Calories', 'FatContent', 'SaturatedFatContent',
                    'CholesterolContent', 'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent',
                    'ProteinContent', 'rating_count', 'rating_mean']
        features += category_unique_values

        pred_df = user_recipe_df.copy()
        pred_df = pred_df.loc[pred_df[excludes_category].sum(axis=1) == 0]

        for col in user_df.columns:
            if col in features:
                pred_df[col] = user_df[col].values[0]

        preds = model.predict(pred_df[features])
        top_k_idx = np.argsort(preds)[::-1][:top_k]
        recommend_df = pred_df.iloc[top_k_idx].reset_index(drop=True)
        print(recommend_df)
        return recommend_df
