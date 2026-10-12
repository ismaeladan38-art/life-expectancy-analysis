"""Life expectancy and income, 1952-2007 (Gapminder).
Run: python scripts/analysis.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

# 1. LOAD AND CLEAN ----------------------------------------------------------
df = pd.read_csv("data/gapminder_raw.csv")
print("Shape:", df.shape)
print("Missing values:\n", df.isna().sum())
print("Duplicate rows:", df.duplicated().sum())
print("Duplicate country-year pairs:", df.duplicated(["country", "year"]).sum())

df = df.drop_duplicates(["country", "year"]).copy()

# The raw file mixes 5-year census points with sparse extra years, and not every
# country has every year. For fair comparisons over time, keep the 12 standard
# years (1952, 1957, ..., 2007) and only countries observed in all of them.
df = df[df["year"].isin(range(1952, 2008, 5))]
n_years = df.groupby("country")["year"].transform("nunique")
df = df[n_years == 12].copy()
print("Balanced panel:", df["country"].nunique(), "countries x 12 years =", len(df), "rows")
df["log_gdp"] = np.log10(df["gdpPercap"])
df.to_csv("data/gapminder_clean.csv", index=False)

# 2. CONTINENT TRENDS -------------------------------------------------------
cont = df.groupby(["continent", "year"])["lifeExp"].mean().unstack(0)
print("\nMean life expectancy by continent:\n", cont.round(1).iloc[[0, -1]])

plt.figure(figsize=(8, 5))
for c in cont.columns:
    plt.plot(cont.index, cont[c], marker="o", label=c)
plt.title("Mean life expectancy by continent, 1952-2007")
plt.xlabel("Year"); plt.ylabel("Life expectancy (years)"); plt.legend()
plt.tight_layout(); plt.savefig("images/01_continent_trends.png", dpi=150); plt.close()

# 3. INCOME VS LIFE EXPECTANCY (2007) ---------------------------------------
d07 = df[df["year"] == 2007]
r = d07["log_gdp"].corr(d07["lifeExp"])
slope, intercept = np.polyfit(d07["log_gdp"], d07["lifeExp"], 1)
r2 = r ** 2
print(f"\n2007: Pearson r (log10 GDP, life exp) = {r:.3f}, R2 = {r2:.3f}")
print(f"Slope = {slope:.2f} years per 10x income; intercept = {intercept:.2f}")

plt.figure(figsize=(8, 5))
sns.scatterplot(data=d07, x="gdpPercap", y="lifeExp", hue="continent",
                size="pop", sizes=(20, 600), alpha=0.7, legend="brief")
plt.xscale("log")
plt.title("Income and life expectancy, 2007")
plt.xlabel("GDP per capita (log scale, USD)"); plt.ylabel("Life expectancy (years)")
plt.tight_layout(); plt.savefig("images/02_income_vs_life_2007.png", dpi=150); plt.close()

# 4. GAP BETWEEN AFRICA AND THE REST ---------------------------------------
afr = df[df.continent == "Africa"].groupby("year")["lifeExp"].mean()
oth = df[df.continent != "Africa"].groupby("year")["lifeExp"].mean()
gap = (oth - afr)
print("\nGap (rest of world minus Africa), years:\n", gap.round(1).to_string())

# 5. ETHIOPIA VS AFRICA -----------------------------------------------------
eth = df[df.country == "Ethiopia"].set_index("year")
print("\nEthiopia life expectancy:\n", eth["lifeExp"].iloc[[0, -1]].round(1).to_string())
print("Africa mean:\n", afr.iloc[[0, -1]].round(1).to_string())

plt.figure(figsize=(8, 5))
plt.plot(eth.index, eth["lifeExp"], marker="o", label="Ethiopia")
plt.plot(afr.index, afr.values, marker="s", label="Africa (mean)")
plt.title("Life expectancy: Ethiopia vs Africa average")
plt.xlabel("Year"); plt.ylabel("Life expectancy (years)"); plt.legend()
plt.tight_layout(); plt.savefig("images/03_ethiopia_vs_africa.png", dpi=150); plt.close()

# 6. OUTLIERS: countries above/below the income-predicted life expectancy ---
d07 = d07.assign(pred=intercept + slope * d07["log_gdp"])
d07["residual"] = d07["lifeExp"] - d07["pred"]
print("\nLargest positive residuals (live longer than income predicts):")
print(d07.nlargest(5, "residual")[["country", "continent", "gdpPercap", "lifeExp", "residual"]].round(1).to_string(index=False))
print("\nLargest negative residuals:")
print(d07.nsmallest(5, "residual")[["country", "continent", "gdpPercap", "lifeExp", "residual"]].round(1).to_string(index=False))
