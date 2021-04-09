library(ggridges)
library(tidyverse)
library(purrr)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

local_coef2 <- read_sf('Spatial_Emissions/outputs/local_coefficients_2007-17.shp') %>% 
  data_frame() %>% 
  select(-MSOA, -geometry) %>% 
  gather('Year', 'Local_Coef') %>%
  na.omit() %>%
  mutate(Year = str_sub(Year, 2, 5))

global_coef <- c()
years = c(2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017)
years_list = c()
for (yr in years){
  temp <- read_csv(paste('Spatial_Emissions/outputs/GWR/coef_', yr, '.csv', sep=''))
  global_coef[yr-2006] <- temp$Global[1]
  years_list[yr-2006] <- paste(yr)
}

global_data <- data_frame(Year=years_list) %>%
  mutate(global = global_coef)

fig <- ggplot() +
  geom_density_ridges_gradient(data=local_coef2, aes(y=Year, x=Local_Coef)) +
  scale_x_continuous(name = 'Local Coefficient') +
  theme_classic()

density_lines <-
  local_coef2 %>% 
  left_join(global_data, by='Year') %>%
  mutate(group = as.integer(factor(Year))) %>% 
  left_join(ggplot_build(fig) %>% purrr::pluck("data", 1), on = "group") %>% 
  group_by(group) %>%
  summarise(x_mean = first(global), 
            density = approx(x, density, first(x_mean))$y, 
            scale = first(scale), 
            iscale = first(iscale))

fig +
  geom_segment(data = density_lines, aes(x = global_coef, y = group, xend = global_coef, 
                                         yend = group + density * scale * iscale),
               color='red')
ggsave('Spatial_Emissions/outputs/GWR_LC_density_ridges1.png')

fig + geom_point(data = density_lines, aes(x=global_coef, y=group+0.5), color='red', size=2)
ggsave('Spatial_Emissions/outputs/GWR_LC_density_ridges2.png')


# prdcited vs. baseline
pred_data <- read_csv('data/processed/pred_values_total_ghg.csv') 
means <- read_csv('data/processed/pred_values_means.csv') %>%
  mutate(Kind=X1) %>% select(-X1)

all <- read_csv('data/processed/pred_values_total_ghg.csv') %>%
  gather('Kind', 'GHG', c(May_policy:Control_2017)) %>%
  mutate(year = ifelse(Kind == 'Control_2017', 'Control', 'Reduction only')) %>%
  mutate(year = ifelse((Kind == 'May_policy' | Kind == 'Nov_policy'), 'Incl. payment schemes', year))

policy <- pred_data %>%
  select(Nov_policy, May_policy, Control_2017) %>%
  gather('Kind', 'GHG', c(Nov_policy:Control_2017)) %>%
  mutate(year = ifelse(Kind == 'Control_2017', '2017', '2020'))

no_policy <- pred_data %>%
  select(-Nov_policy, -May_policy) %>%
  gather('Kind', 'GHG', c(May_reg:Control_2017)) %>%
  mutate(year = ifelse(Kind == 'Control_2017', '2017', '2020'))
  
# all
all_plot <- ggplot() +
  geom_density_ridges_gradient(data=all, aes(y=Kind, x=GHG, fill=year)) +
  scale_x_continuous(name = 'tCO2e per capita') +
  scale_y_discrete(name = '', label=c('2017', 'May 2020', 'May 2020', 'November 2020', 'November 2020')) +
  scale_fill_manual(name = 'Year', values=c('#A7D0E3', '#DB6F57', '#F6B799')) +
  theme_classic()

density_lines <- all %>% 
  left_join(means, by='Kind') %>%
  mutate(group = as.integer(factor(Kind))) %>% 
  left_join(ggplot_build(all_plot) %>% purrr::pluck("data", 1), on = "group") %>% 
  group_by(group) %>%
  summarise(x_mean = first(mean_ghg), 
            density = approx(x, density, first(x_mean))$y, 
            scale = first(scale), 
            iscale = first(iscale))

all_plot +
  geom_segment(data=density_lines, aes(x = x_mean, y = group, xend = x_mean, 
                                       yend = group + density * scale * iscale), color='#B61E2E')
ggsave('Spatial_Emissions/outputs/predicted_ridges_all.png')



# policy
policy_plot <- ggplot() +
  geom_density_ridges_gradient(data=policy, aes(y=Kind, x=GHG, fill=year)) +
  scale_x_continuous(name = 'tCO2e per capita') +
  scale_y_discrete(name = '', label=c('2017', 'May 2020', 'November 2020')) +
  scale_fill_manual(name = 'Year', values=c('#A7D0E3', '#F6B799')) +
  theme_classic()

density_lines <- policy %>% 
  left_join(means, by='Kind') %>%
  mutate(group = as.integer(factor(Kind))) %>% 
  left_join(ggplot_build(policy_plot) %>% purrr::pluck("data", 1), on = "group") %>% 
  group_by(group) %>%
  summarise(x_mean = first(mean_ghg), 
            density = approx(x, density, first(x_mean))$y, 
            scale = first(scale), 
            iscale = first(iscale))

policy_plot +
  geom_segment(data=density_lines, aes(x = x_mean, y = group, xend = x_mean, 
                                       yend = group + density * scale * iscale), color='#B61E2E')
ggsave('Spatial_Emissions/outputs/predicted_ridges_policy.png')


# policy
np_plot <- ggplot() +
  geom_density_ridges_gradient(data=no_policy,
                               aes(y=Kind, x=GHG, fill=year)) +
  scale_x_continuous(name = 'tCO2e per capita') +
  scale_y_discrete(name = '', label=c('2017', 'May 2020', 'November 2020')) +
  scale_fill_manual(name = 'Year', values=c('#A7D0E3', '#F6B799')) +
  theme_classic()

density_lines <-no_policy %>% 
  left_join(means, by='Kind') %>%
  mutate(group = as.integer(factor(Kind))) %>% 
  left_join(ggplot_build(np_plot) %>% purrr::pluck("data", 1), on = "group") %>% 
  group_by(group) %>%
  summarise(x_mean = first(mean_ghg), 
            density = approx(x, density, first(x_mean))$y, 
            scale = first(scale), 
            iscale = first(iscale))

np_plot +
  geom_segment(data=density_lines, aes(x = x_mean, y = group, xend = x_mean, 
                                       yend = group + density * scale * iscale), color='#B61E2E')
ggsave('Spatial_Emissions/outputs/predicted_ridges_nopolicy.png')
