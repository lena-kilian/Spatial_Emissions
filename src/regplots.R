# Required libraries.
library(tidyverse)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis/")
# -------------------------------------------
# D A T A
# -------------------------------------------

data <- read_csv("data/processed/lad_avg_all.csv")

# -------------------------------------------
# 2017 by products
# -------------------------------------------
plot.margin = unit(c(2, 2, 2, 2), "cm")
p <- ggplot(data, aes(x=income, y=ghg, colour=RGN11NM)) + 
  geom_smooth(method='lm') 
p + facet_grid(product ~ year)
ggsave("Spatial_Emissions/outputs/lad_avg_all.png")

#items = c('grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg')

items = c('food (other)', 'food (ab)', 'other','other home', 'home energy', 'trsprt (priv.)', 'trsprt (rail, bus)', 'trsprt (air)', 'trsprt (water)', 'ccp 9', 'eating out', 'ccp 12', 'total_ghg')

for (item in items){
  item_data = data %>% filter(product == item)
  p <- ggplot(item_data, aes(x=income, y=ghg, colour=RGN11NM)) + 
    geom_smooth(method='lm', size=0.5, se=FALSE) +
    geom_point(size=0.5, alpha=0.2) +
    theme_bw()
  p + facet_grid(product ~ year)
  ggsave(paste("Spatial_Emissions/outputs/lad_avg_all_", item, ".png", sep=''))
}


#items = c('grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg')
for (item in items){
  item_data = data %>% filter(product == item) %>% arrange(c(year, RGN11NM))
  p <- ggplot(item_data, aes(x=income, y=ghg)) + 
    geom_smooth(method='lm', size=0.5) +
    geom_point(size=0.5, alpha=0.4) +
    theme_bw()
  p + facet_wrap(year ~ RGN11NM)
  ggsave(paste("Spatial_Emissions/outputs/lad_avg_all_v2_", item, ".png", sep=''))
}


incomes <-read_csv("data/processed/GHG_Estimates/LAD_incomes.csv") %>%
  mutate(income_lcfs = `Income anonymised`,
         level = 'Level 1',
         year_str = as.character(year))

p <- ggplot(incomes, aes(x=income_lcfs, y=income_disp, colour=RGN11NM)) + 
  geom_smooth(method='lm', size=0.5, se=FALSE) +
  geom_point(size=0.5, alpha=0.2) +
  theme_bw()
p + facet_grid(level ~ year)

p <- ggplot(incomes, aes(x=income_lcfs, y=income_disp)) + 
  geom_smooth(method='lm', size=0.5, se=FALSE) +
  geom_point(size=0.5, alpha=0.2) +
  theme_bw()
p + facet_grid(RGN11NM ~ year)


p <- ggplot(incomes, aes(x=income_lcfs, y=income_disp, colour=year_str)) + 
  geom_smooth(method='lm', size=0.5, se=FALSE) +
  geom_point(size=0.5, alpha=0.2) +
  theme_bw()
p + facet_grid(level ~ RGN11NM)


