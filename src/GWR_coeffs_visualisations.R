library(ggridges)
library(tidyverse)
library(purrr)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

# regression plot
all_data <- read_csv('Spatial_Emissions/outputs/GWR/local_coeffs/all_for_plot.csv') %>%
  mutate(var = paste(transport, pred, income_controlled, sep='_'),
         group = as.integer(factor(var)),
         income_controlled = ifelse(pred=='totalinc', TRUE, income_controlled)) %>%
  #mutate(local_coeffs = ifelse(var == 'Flights_totalwork_FALSE', NA, local_coeffs),
  ##       local_coeffs = ifelse(var == 'Flights_totalwork_TRUE', NA, local_coeffs),
  #       local_coeffs = ifelse(var == 'Flights_AI2015ln_FALSE', NA, local_coeffs),
  #       local_coeffs = ifelse(var == 'Flights_AI2015ln_True', NA, local_coeffs)) %>%
  filter(var != 'Flights_totalwork_FALSE' & 
           var != 'Flights_totalwork_TRUE' &
           var != 'Flights_AI2015ln_FALSE' &
           var != 'Flights_AI2015ln_TRUE') %>%
  mutate(inc = ifelse(income_controlled == TRUE, 'Income controlled', 'Income not controlled'))

order <- all_data %>% 
  select(pred) %>% 
  distinct() %>%
  mutate(order = seq(6, 1),
         order = ifelse(pred == 'totalinc', 7, order)) %>%
  cbind(data_frame('predictors' = c('Public Transport Access', 'Population not limited in day-to-day activities', 
                                    'Population aged 65 or older', 'Population aged 14 or younger',
                                    'Distance to workplace', 'Income')))

my_cols <- all_data %>% 
  select(transport) %>% 
  distinct() %>% 
  arrange(transport) %>% 
  cbind(data_frame('colours' = c('#6D0021', '#C54A43', '#F1B593'))) %>% #'#9A576D'
  cbind(data_frame('Transport Type' = c('Car/van purchases and motoring oils', 'Flights', 'Rail and bus')))

all_data <- all_data %>% left_join(order, by='pred') %>% left_join(my_cols, by='transport') %>% mutate(var = paste(order, pred, `Transport Type`, sep=' '))

y_labels <- all_data %>% select(var, predictors) %>% distinct() %>% arrange(var)
ggplot() +
  geom_density_ridges_gradient(data=all_data, aes(y=var, x=local_coeffs, fill=`Transport Type`)) +
  scale_fill_manual(values = cols$colours) +
  scale_y_discrete(name=' ', labels = y_labels$predictors, breaks=y_labels$var) +
  xlab('Local Coefficient') +
  theme_classic() + 
  facet_grid(. ~ inc) +
  xlim(-13, 13) + 
  theme(legend.position = c('bottom'), text = element_text(colour="black", size=17, family="Times New Roman"))

ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_all.png', sep='_'))


