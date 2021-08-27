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
  mutate(inc = ifelse(income_controlled == TRUE, 'Income controlled', 'Income not controlled'),
         label_3 = ifelse(income_controlled == TRUE, 'y', 'n'))

order <- all_data %>% 
  select(pred) %>% 
  distinct() %>%
  mutate(order = seq(7, 1),
         order = ifelse(pred == 'totalinc', 8, order)) %>%
  cbind(data_frame('predictors' = c('Public Transport Access', 'Population not limited in day-to-day activities', 
                                    'Population aged 65 or older', 'Population aged 14 or younger', 'Population identifying as BAME',
                                    'Distance to workplace', 'Income'))) %>%
  cbind(data_frame('label_2' = c('TD', 'LD', '65', '14', 'E', 'Dis', 'Inc')))
  

my_cols <- all_data %>% 
  select(transport) %>% 
  distinct() %>% 
  arrange(transport) %>% 
  cbind(data_frame('colours' = c('#6D0021', '#C54A43', '#F1B593'))) %>% #'#9A576D'
  cbind(data_frame('Transport Type' = c('Car/van purchases and motoring oils', 'Flights', 'Rail and bus'))) %>%
  cbind(data_frame('label_1' = c('C', 'F', 'R')))

all_data <- all_data %>% left_join(order, by='pred') %>% left_join(my_cols, by='transport') %>% 
  mutate(var = paste(order, pred, `Transport Type`, sep=' '),
         label = paste(label_1, label_2, label_3, sep='-'))

text_data <- all_data %>% select(transport, pred, income_controlled, var, group, inc, predictors, label) %>% distinct() %>%
  mutate(text_pos = -10.8)

y_labels <- all_data %>% select(var, predictors) %>% distinct() %>% arrange(var)
ggplot() +
  geom_density_ridges_gradient(data=all_data, aes(y=var, x=local_coeffs, fill=`Transport Type`)) +
  scale_fill_manual(name = '', values = my_cols$colours) +
  scale_y_discrete(name=' ', labels = y_labels$predictors, breaks=y_labels$var) +
  guides(fill = guide_legend(override.aes = list(shape = 16))) +
  geom_text(data=text_data, aes(y=var, vjust=-0.5, x=text_pos, label=label), colour="black", size=4, family="Times New Roman") + 
  xlab('Local Coefficient') +
  theme_classic() + 
  facet_grid(. ~ inc) +
  xlim(-13, 13) + 
  geom_vline(xintercept=c(0,0), linetype="dotted") +
  theme(legend.position = c('bottom'), text = element_text(colour="black", size=17, family="Times New Roman")) 

ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_all.png', sep='_'))


