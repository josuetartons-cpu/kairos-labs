# ============================================================
# 02_analisis_desacoplamiento.R
# Kairos — Guatemala: crecimiento económico y emisiones de CO2
# ============================================================


# ------------------------------------------------------------
# 1. CARGAR FUNCIONES Y LIBRERIAS
# ------------------------------------------------------------

source("01_conexion_banco_mundial.R")

library(dplyr)
library(tidyr)
library(ggplot2)


# ------------------------------------------------------------
# 2. DESCARGAR DATOS PRINCIPALES
# ------------------------------------------------------------

pib_real_gt <- get_wb_data(
  "GT",
  "NY.GDP.MKTP.KD",
  2000,
  2024
)

co2_total_gt <- get_wb_data(
  "GT",
  "EN.GHG.CO2.MT.CE.AR5",
  2000,
  2024
)

renovables_gt <- get_wb_data(
  "GT",
  "EG.FEC.RNEW.ZS",
  2000,
  2022
)

renovables_electricidad_gt <- get_wb_data(
  "GT",
  "EG.ELC.RNEW.ZS",
  2000,
  2024
)


# ------------------------------------------------------------
# 3. CONSTRUIR DATASET DE DESACOPLAMIENTO
# ------------------------------------------------------------

desacoplamiento_gt <- pib_real_gt %>%
  select(
    iso3,
    pais,
    anio,
    PIB_real = valor
  ) %>%
  left_join(
    co2_total_gt %>%
      select(
        iso3,
        anio,
        CO2_total = valor
      ),
    by = c("iso3", "anio")
  ) %>%
  arrange(anio) %>%
  mutate(
    crecimiento_PIB =
      100 * (PIB_real / lag(PIB_real) - 1),

    crecimiento_CO2 =
      100 * (CO2_total / lag(CO2_total) - 1),

    intensidad_carbono =
      CO2_total / PIB_real,

    indice_PIB =
      100 * PIB_real / first(PIB_real),

    indice_CO2 =
      100 * CO2_total / first(CO2_total)
  )


# ------------------------------------------------------------
# 4. CAMBIOS LOGARITMICOS ANUALES
# ------------------------------------------------------------

cambios_gt <- desacoplamiento_gt %>%
  arrange(anio) %>%
  mutate(
    dlog_PIB =
      100 * (
        log(PIB_real) -
        lag(log(PIB_real))
      ),

    dlog_CO2 =
      100 * (
        log(CO2_total) -
        lag(log(CO2_total))
      )
  )


# ------------------------------------------------------------
# 5. ENERGIA RENOVABLE E INTENSIDAD DE CARBONO
# ------------------------------------------------------------

energia_gt <- desacoplamiento_gt %>%
  left_join(
    renovables_gt %>%
      select(
        iso3,
        anio,
        renovables = valor
      ),
    by = c("iso3", "anio")
  ) %>%
  mutate(
    intensidad_kg_usd =
      intensidad_carbono * 1e9
  )


# ------------------------------------------------------------
# 6. ELECTRICIDAD RENOVABLE E INTENSIDAD DE CARBONO
# ------------------------------------------------------------

electricidad_gt <- desacoplamiento_gt %>%
  left_join(
    renovables_electricidad_gt %>%
      select(
        iso3,
        anio,
        renovables_electricidad = valor
      ),
    by = c("iso3", "anio")
  ) %>%
  mutate(
    intensidad_kg_usd =
      intensidad_carbono * 1e9
  )


# ============================================================
# 7. CREAR CARPETAS DE OUTPUT
# ============================================================

dir.create(
  "figures",
  showWarnings = FALSE
)

dir.create(
  "results",
  showWarnings = FALSE
)


# ============================================================
# 8. FIGURA 1
# PIB REAL Y EMISIONES DE CO2
# ============================================================

grafica_indices <- desacoplamiento_gt %>%
  select(
    anio,
    indice_PIB,
    indice_CO2
  ) %>%
  pivot_longer(
    cols = c(
      indice_PIB,
      indice_CO2
    ),
    names_to = "serie",
    values_to = "indice"
  ) %>%
  mutate(
    serie = case_when(
      serie == "indice_PIB" ~ "PIB real",
      serie == "indice_CO2" ~ "Emisiones de CO2"
    )
  )


figura_01 <- ggplot(
  grafica_indices,
  aes(
    x = anio,
    y = indice,
    linetype = serie
  )
) +
  geom_line(
    linewidth = 1.2
  ) +
  labs(
    title =
      "Guatemala: crecimiento económico y emisiones de CO2",

    subtitle =
      "Índice 2000 = 100",

    x =
      "Año",

    y =
      "Índice",

    linetype =
      NULL,

    caption =
      "Fuente: elaboración propia con datos del Banco Mundial."
  ) +
  theme_minimal(
    base_size = 13
  ) +
  theme(
    legend.position =
      "bottom",

    plot.title =
      element_text(
        face = "bold"
      )
  )


# ============================================================
# 9. FIGURA 2
# VARIACIONES ANUALES DEL PIB Y CO2
# ============================================================

figura_02 <- ggplot(
  cambios_gt %>%
    filter(
      !is.na(dlog_PIB),
      !is.na(dlog_CO2)
    ),
  aes(
    x = dlog_PIB,
    y = dlog_CO2
  )
) +
  geom_point(
    size = 2.8
  ) +
  geom_text(
    aes(
      label = anio
    ),
    nudge_y = 0.45,
    size = 3
  ) +
  geom_smooth(
    method = "lm",
    se = FALSE,
    linewidth = 1
  ) +
  labs(
    title =
      "Guatemala: variaciones anuales del PIB real y del CO2",

    subtitle =
      "Cambios logarítmicos, 2001–2024",

    x =
      "Cambio anual del PIB real (%)",

    y =
      "Cambio anual de las emisiones de CO2 (%)",

    caption =
      paste(
        "2020–2021 constituyen observaciones extraordinarias",
        "asociadas al shock de pandemia y recuperación."
      )
  ) +
  theme_minimal(
    base_size = 13
  ) +
  theme(
    plot.title =
      element_text(
        face = "bold"
      ),

    plot.caption =
      element_text(
        hjust = 0
      )
  )


# ============================================================
# 10. FIGURA 3
# RENOVABLES E INTENSIDAD DE CARBONO
# ============================================================

figura_03 <- ggplot(
  energia_gt %>%
    filter(
      !is.na(renovables)
    ),
  aes(
    x = renovables,
    y = intensidad_kg_usd
  )
) +
  geom_point(
    size = 2.8
  ) +
  geom_text(
    aes(
      label = anio
    ),
    nudge_y = 0.002,
    size = 3
  ) +
  geom_smooth(
    method = "lm",
    se = TRUE,
    linewidth = 1
  ) +
  labs(
    title =
      "Guatemala: energía renovable e intensidad de carbono",

    subtitle =
      "Datos disponibles 2000–2021",

    x =
      "Energía renovable (% del consumo final)",

    y =
      "Intensidad de carbono (kg CO2e por US$ de PIB real)",

    caption =
      "Fuente: elaboración propia con datos del Banco Mundial."
  ) +
  theme_minimal(
    base_size = 13
  ) +
  theme(
    plot.title =
      element_text(
        face = "bold"
      ),

    plot.caption =
      element_text(
        hjust = 0
      )
  )


# ============================================================
# 11. FIGURA 4
# ELECTRICIDAD RENOVABLE E INTENSIDAD DE CARBONO
# ============================================================

figura_04 <- ggplot(
  electricidad_gt %>%
    filter(
      !is.na(renovables_electricidad)
    ),
  aes(
    x = renovables_electricidad,
    y = intensidad_kg_usd
  )
) +
  geom_point(
    size = 2.8
  ) +
  geom_text(
    aes(
      label = anio
    ),
    nudge_y = 0.002,
    size = 3
  ) +
  geom_smooth(
    method = "lm",
    se = TRUE,
    linewidth = 1
  ) +
  labs(
    title =
      "Guatemala: electricidad renovable e intensidad de carbono",

    subtitle =
      "Generación renovable e intensidad de carbono, 2000–2021",

    x =
      "Electricidad renovable (% de la generación)",

    y =
      "Intensidad de carbono (kg CO2e por US$ de PIB real)",

    caption =
      "Fuente: elaboración propia con datos del Banco Mundial."
  ) +
  theme_minimal(
    base_size = 13
  ) +
  theme(
    plot.title =
      element_text(
        face = "bold"
      ),

    plot.caption =
      element_text(
        hjust = 0
      )
  )


# ============================================================
# 12. EXPORTAR FIGURAS
# ============================================================

ggsave(
  filename =
    "figures/01_pib_emisiones.png",

  plot =
    figura_01,

  width =
    10,

  height =
    7,

  dpi =
    300,

  bg =
    "white"
)


ggsave(
  filename =
    "figures/02_variaciones_anuales.png",

  plot =
    figura_02,

  width =
    10,

  height =
    7,

  dpi =
    300,

  bg =
    "white"
)


ggsave(
  filename =
    "figures/03_renovables_intensidad.png",

  plot =
    figura_03,

  width =
    10,

  height =
    7,

  dpi =
    300,

  bg =
    "white"
)


ggsave(
  filename =
    "figures/04_electricidad_renovable.png",

  plot =
    figura_04,

  width =
    10,

  height =
    7,

  dpi =
    300,

  bg =
    "white"
)


# ============================================================
# 13. GUARDAR RESULTADOS BASE
# ============================================================

write.csv(
  desacoplamiento_gt,
  "results/desacoplamiento_gt.csv",
  row.names = FALSE
)

write.csv(
  cambios_gt,
  "results/cambios_gt.csv",
  row.names = FALSE
)

write.csv(
  energia_gt,
  "results/energia_gt.csv",
  row.names = FALSE
)

write.csv(
  electricidad_gt,
  "results/electricidad_gt.csv",
  row.names = FALSE
)


# ============================================================
# 14. VERIFICACION FINAL
# ============================================================

cat(
  "\n=============================================\n",
  "KAIROS — EXPERIMENTO COMPLETADO\n",
  "=============================================\n\n",

  "Figuras generadas:\n",
  "figures/01_pib_emisiones.png\n",
  "figures/02_variaciones_anuales.png\n",
  "figures/03_renovables_intensidad.png\n",
  "figures/04_electricidad_renovable.png\n\n",

  "Resultados generados:\n",
  "results/desacoplamiento_gt.csv\n",
  "results/cambios_gt.csv\n",
  "results/energia_gt.csv\n",
  "results/electricidad_gt.csv\n\n"
)


print(
  list.files(
    "figures"
  )
)

print(
  list.files(
    "results"
  )
)