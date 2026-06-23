# Set custom theme to use in all my plots (to make sure things are big enough,
# so in latex document they are properly visualized)

theme_thesis <- function() {
  theme_bw(base_size = 16) +
    theme(
      plot.title = element_text(size = 18, face = "bold"),
      plot.subtitle = element_text(size = rel(0.9)),
      axis.title = element_text(size = 16, face="bold"),
      axis.text = element_text(size = 14),
      legend.title = element_text(size = 15, face = "bold"),
      legend.text = element_text(size = 13),
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      strip.text = element_text(size = 15, face = "bold"),
      strip.background = element_rect(fill = "grey95")
    )
}