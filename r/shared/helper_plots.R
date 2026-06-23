library(tidyverse)

path <- "/home/miguel/6.Projects/Thesis/src/scripts/output/Sioux_Falls.net.csv"
saving_path <- "/home/miguel/6.Projects/Thesis/Thesis_Document/media/networks/Histogram_length_links/1nd.net.png"
df <- read_csv(path, col_names = "Length")
min_length <- min(df$Length)
max_length <- max(df$Length)
mean_length <- round(mean(df$Length),2)
text <- paste("Mean Length Links",mean_length,"m")

ggplot(
  data = df,
  mapping = aes(x = Length)
) +
  geom_histogram() +
  labs(
    title = "Distribution of Links Lengths",
    x = "Length (m)",
    y = "Number of links"
  ) +
  geom_vline(xintercept = mean_length, color = "red", linewidth = 2) +
  annotate(
    geom = "label", 
    x = mean_length - 10,
    y = 1,
    label = text
    ) +
  theme_classic()
  

ggsave(saving_path)
