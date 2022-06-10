library(tidyverse)
library(purrr)
library(tm)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

# new with wide format
all_data <- read_csv('Spatial_Emissions/outputs/GWR/local_coeffs/all_for_plot.csv') %>%
  mutate(income_controlled = ifelse(pred=='totalinc', TRUE, income_controlled),
         colours = ifelse(income_controlled == TRUE, '#C54A43', '#F1B593'),
         label_3 = ifelse(income_controlled == TRUE, 'y', 'n'),
         local_coef_count = ifelse(local_coeffs > 0, 'above_0', 'is_0'),
         local_coef_count = ifelse(local_coeffs < 0, 'below_0', local_coef_count)) %>%
  filter(income_controlled == TRUE,
         !(pred == 'AI2015ln' & transport =='Flights'),
         !(pred == 'totalwork' & transport =='Flights'))


count <- all_data %>%
  group_by(local_coef_count, transport, pred) %>%
  count() %>%
  ungroup() %>%
  spread(local_coef_count, n)

below_0 <- count %>%
  group_by(pred) %>%
  top_n(1, below_0) %>%
  ungroup()

above_0 <- count %>%
  group_by(pred) %>%
  top_n(1, above_0) %>%
  ungroup()