import asyncio

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from app.repositories.db.parser import ParserRepository


class ReviewsPlotter:
    @classmethod
    async def plot_avg_rating_per_year(
            cls,
            model: str | None = None,
            brand: str | None = None,
            min_reviews: int = 3,
            title: str = "Average Rating by Year") -> None:

        data = await ParserRepository.get_avg_rating_per_year(
            model=model,
            brand=brand,
            min_reviews_per_year=min_reviews
        )

        if not data:
            print("No data found for given parameters.")
            return

        df = pd.DataFrame(data)

        sns.set_theme(style="whitegrid")

        plt.figure(figsize=(10, 5))
        sns.lineplot(x='year', y='avg_rating', data=df, marker='o')

        if model:
            plot_title = f'{title} for {model.capitalize()}'
        elif brand:
            plot_title = f'{title} for {brand.capitalize()}'
        else:
            plot_title = title

        plt.title(plot_title)
        plt.xlabel('Year')
        plt.ylabel('Average Rating')
        plt.ylim(4.0, 4.7)
        plt.xticks(df['year'])

        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    # asyncio.run(ReviewsPlotter.plot_avg_rating_per_year(model='corolla'))
    asyncio.run(ReviewsPlotter.plot_avg_rating_per_year(brand='toyota'))
