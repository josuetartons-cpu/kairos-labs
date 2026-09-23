# ============================================================
# 01_conexion_banco_mundial.R
# Conexion a la API del Banco Mundial
# ============================================================


# ------------------------------------------------------------
# 1. Librerias
# ------------------------------------------------------------

library(jsonlite)
library(dplyr)


# ------------------------------------------------------------
# 2. Funcion para descargar datos del Banco Mundial
# ------------------------------------------------------------

get_wb_data <- function(country, indicator, start, end) {
  
  url <- paste0(
    "https://api.worldbank.org/v2/country/",
    country,
    "/indicator/",
    indicator,
    "?format=json",
    "&date=", start, ":", end,
    "&per_page=1000"
  )
  
  respuesta <- fromJSON(url)
  
  # Verificar que la API haya devuelto datos
  if (length(respuesta) < 2 || is.null(respuesta[[2]])) {
    stop(
      paste(
        "La API no devolvio datos para el indicador:",
        indicator
      )
    )
  }
  
  datos <- respuesta[[2]]
  
  # Estructurar los datos
  resultado <- data.frame(
    iso3 = datos$countryiso3code,
    pais = datos$country$value,
    anio = as.integer(datos$date),
    valor = datos$value
  )
  
  # Ordenar cronologicamente
  resultado <- resultado[order(resultado$anio), ]
  
  # Reiniciar indices
  rownames(resultado) <- NULL
  
  return(resultado)
}
# ============================================================
# 2. CONSTRUCCIÓN DEL DATASET DE GUATEMALA
# ============================================================

guatemala <- get_wb_data(
  "GT",
  "NY.GDP.PCAP.CD",
  2000,
  2024
)

gdp_growth <- get_wb_data(
  "GT",
  "NY.GDP.MKTP.KD.ZG",
  2000,
  2024
)

inflacion <- get_wb_data(
  "GT",
  "FP.CPI.TOTL.ZG",
  2000,
  2024
)

desempleo <- get_wb_data(
  "GT",
  "SL.UEM.TOTL.ZS",
  2000,
  2024
)

co2 <- get_wb_data(
  "GT",
  "EN.GHG.CO2.PC.CE.AR5",
  2000,
  2024
)


# ============================================================
# 3. RENOMBRAR VARIABLES
# ============================================================

names(guatemala)[4] <- "PIB_pc"
names(gdp_growth)[4] <- "crecimiento"
names(inflacion)[4] <- "inflacion"
names(desempleo)[4] <- "desempleo"
names(co2)[4] <- "CO2_pc"


# ============================================================
# 4. UNIFICAR DATASET
# ============================================================

economia_gt <- merge(
  guatemala,
  gdp_growth,
  by = c("iso3", "pais", "anio")
)

economia_gt <- merge(
  economia_gt,
  inflacion,
  by = c("iso3", "pais", "anio")
)

economia_gt <- merge(
  economia_gt,
  desempleo,
  by = c("iso3", "pais", "anio")
)

economia_gt <- merge(
  economia_gt,
  co2,
  by = c("iso3", "pais", "anio")
)


# ============================================================
# 5. VERIFICACIÓN DE DATOS
# ============================================================

str(economia_gt)

summary(economia_gt)

colSums(is.na(economia_gt))

nrow(economia_gt)


indicadores <- fromJSON(
  "https://api.worldbank.org/v2/indicator?format=json&per_page=1000"
)

names(indicadores)