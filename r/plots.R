library(arrow)
library(tidyverse)

statistics_parquet_path <- "/home/miguel/6.Projects/Thesis/data/processed/statistics.parquet"
statistics_plot_path <- "/home/miguel/6.Projects/Thesis/output/figures/statistics.png"
dpi = 300
width = 10
height = 6

#################################################
# 1. "Statistics" parquet file
#################################################
df_statistics <- read_parquet(statistics_parquet_path)

# Data wrangling
df_statistics <- df_statistics |> pivot_longer(
  cols = !episode,
  names_to = "metric",
  values_to = "value"
)

# Plot
# scales = "free_y": To allow each subplot to have its own independent y-axis range
statistics_plot <- ggplot(
  data = df_statistics,
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

# Save plot
ggsave(filename = statistics_plot_path, plot = statistics_plot, dpi = dpi, width = width, height = height)

#################################################
# 2. "Vehroute" parquet file
#################################################
vehroute_parquet_path <- "/home/miguel/6.Projects/Thesis/data/processed/vehroute.parquet"
vehroute_plot_1_path <- "/home/miguel/6.Projects/Thesis/output/figures/vehroute_1.png"
vehroute_plot_2_path <- "/home/miguel/6.Projects/Thesis/output/figures/vehroute_2.png"

df_vehroute <- read_parquet(vehroute_parquet_path)

# lag: Previous edge time
# First edge time = exit_time - 0
df_vehroute <- df_vehroute |> 
  arrange(episode, vehicle_id, exit_times) |> 
  group_by(episode, vehicle_id) |> 
  mutate(
    time_on_edge = exit_times - lag(exit_times, default = 0)
  ) |> 
  ungroup()

############
# FIRST PLOT
############

# Mean time per edge
df_vehroute_plot_1 <- df_vehroute |> 
  group_by(edge) |> 
  summarise(mean_time = mean(time_on_edge)) |> 
  slice_max(mean_time, n = 5)

vehroute_plot_1 <- ggplot(
  data = df_vehroute_plot_1,
  mapping = aes(x = reorder(edge, desc(mean_time)), y = mean_time)
  ) + 
  geom_col() +
  theme_minimal() +
  labs(
    title = "Mean time of top 5 slowest edges over all episodes"
  )

# Save plot
ggsave(filename = vehroute_plot_1_path, plot = vehroute_plot_1, dpi = dpi, width = width, height = height)

############
# SECOND PLOT
############

# Plot over episodes (top 5 slowest edges)
top_5_slowest_edges <- df_vehroute_plot_1 |> pull(edge)

df_vehroute_plot_2 <- df_vehroute |> filter(
  edge %in% top_5_slowest_edges
) |> 
  group_by(episode, edge) |> 
  summarise(mean_time = mean(time_on_edge))

vehroute_plot_2 <- ggplot(
  data = df_vehroute_plot_2,
  mapping = aes(x = episode, y = mean_time)
) +
  geom_line() +
  facet_wrap(~ edge, scales = "free_y") +
  labs(
    title = "Mean time on edge over episodes (5 slowest edges)"
  )

# Save plot
ggsave(filename = vehroute_plot_2_path, plot = vehroute_plot_2, dpi = dpi, width = width, height = height)

  