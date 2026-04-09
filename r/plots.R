library(arrow)
library(tidyverse)

statistics_output_parquet_path <- "~/6.Projects/Thesis/sumo/output/statistics_output/statistics.parquet"
statistics_output_plot_path <- "~/6.Projects/Thesis/sumo/output/statistics_output/statistics_plot.png"
dpi = 300
width = 10
height = 6

#################################################
# 1. Read "statistics output" parquet file
#################################################
df_statistics_output <- read_parquet(statistics_output_parquet_path)

# Plots
df_statistics_output <- df_statistics_output |> pivot_longer(
  cols = !episode,
  names_to = "metric",
  values_to = "value"
)

# scales = "free_y": To allow each subplot to have its own independent y-axis range
statistics_output_plot <- ggplot(
  data = df_statistics_output,
  mapping = aes(x = episode, y = value)
) +
  geom_line(color = "steelblue") +
  facet_wrap(~ metric, scales = "free_y") +
  labs(
    title = "Aggregated metrics over episodes",
    x = "Episode",
    y = "Value"
  ) +
  theme_minimal()

ggsave(filename = statistics_output_plot_path, plot = statistics_output_plot, dpi = dpi, width = width, height = height)

