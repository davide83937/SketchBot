/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "usb_device.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include <math.h>

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim3;
TIM_HandleTypeDef htim4;

/* USER CODE BEGIN PV */
extern uint8_t usb_rx_buffer[64];
extern volatile uint8_t usb_data_ready;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM3_Init(void);
static void MX_TIM4_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

float current_angles[4] = {100.0, 93.0, 75, 171.0};

// VARIABILI VOLATILI PER L'INPUT MANUALE
volatile float target_angle_0 = 100.0;
volatile float target_angle_1 = 93.0;
volatile float target_angle_2 = 75.0;
volatile float target_angle_3 = 171.0;

// Converte l'angolo in tick per il registro CCR (PWM)
// Valori standard: 500 (0°) -> 2500 (180°). Regolali in base ai tuoi servo specifici.
uint32_t get_servo_angle_impulse(float angle) {
    // Sicurezza limiti assoluti
    if (angle > 180.0f) angle = 180.0f;
    if (angle < 0.0f) angle = 0.0f;

    // Calcola il tick esatto tenendo conto dei decimali
    return (uint32_t)(500.0f + (angle * 2000.0f / 180.0f));
}
// Funzione per muovere il motore a una velocità controllata
// delay_ms: regola la velocità (es. 2 = molto veloce, 15 = lento, 30 = lentissimo)
// Nuova funzione fluida e sicura
// Funzione per il movimento fluido e sincronizzato di tutto il braccio
void move_arm_synchronized(TIM_HandleTypeDef *htim, float t0, float t1, float t2, float t3, float max_speed) {

    // 1. Applica i limiti di sicurezza meccanici ai target
    if (t0 > 180.0) t0 = 180.0; if (t0 < 0.0) t0 = 0.0;
    if (t1 > 180.0) t1 = 180.0; if (t1 < 40.0) t1 = 40.0; // Limite sicurezza motore 1
    if (t2 > 180.0) t2 = 180.0; if (t2 < 0.0) t2 = 0.0;
    if (t3 > 180.0) t3 = 180.0; if (t3 < 0.0) t3 = 0.0;

    // 2. Calcola quanta strada deve fare ogni motore (valore assoluto)
    float d0 = fabs(t0 - current_angles[0]);
    float d1 = fabs(t1 - current_angles[1]);
    float d2 = fabs(t2 - current_angles[2]);
    float d3 = fabs(t3 - current_angles[3]);

    // 3. Trova la distanza massima (chi deve fare il percorso più lungo?)
    float max_dist = d0;
    if (d1 > max_dist) max_dist = d1;
    if (d2 > max_dist) max_dist = d2;
    if (d3 > max_dist) max_dist = d3;

    // 4. Se la distanza è piccolissima, siamo praticamente arrivati. Fissa i valori ed esci.
    if (max_dist < 0.7) {
        current_angles[0] = t0;
        current_angles[1] = t1;
        current_angles[2] = t2;
        current_angles[3] = t3;
    }
    else {
        // 5. Il cuore della robotica: Calcolo dei passi proporzionali.
        // Il motore che deve fare più strada si muoverà di 'max_speed'.
        // Gli altri andranno più lenti in proporzione alla loro distanza.
        float step0 = ((t0 - current_angles[0]) / max_dist) * max_speed;
        float step1 = ((t1 - current_angles[1]) / max_dist) * max_speed;
        float step2 = ((t2 - current_angles[2]) / max_dist) * max_speed;
        float step3 = ((t3 - current_angles[3]) / max_dist) * max_speed;

        // 6. Aggiorna le posizioni correnti
        current_angles[0] += step0;
        current_angles[1] += step1;
        current_angles[2] += step2;
        current_angles[3] += step3;
    }

    // 7. Invia i segnali PWM ai timer con la massima precisione (senza cast a uint8_t)
        __HAL_TIM_SET_COMPARE(htim, TIM_CHANNEL_1, get_servo_angle_impulse(current_angles[0]));
        __HAL_TIM_SET_COMPARE(htim, TIM_CHANNEL_2, get_servo_angle_impulse(current_angles[1]));
        __HAL_TIM_SET_COMPARE(htim, TIM_CHANNEL_3, get_servo_angle_impulse(current_angles[2]));
        __HAL_TIM_SET_COMPARE(htim, TIM_CHANNEL_4, get_servo_angle_impulse(current_angles[3]));
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM3_Init();
  MX_TIM4_Init();
  MX_USB_DEVICE_Init();
  /* USER CODE BEGIN 2 */

    // Avvia i 4 canali PWM del TIM4 (PB6, PB7, PB8, PB9)
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_2);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_3);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_4);

    // FINE CORSA SOFTWARE INIZIALE: Protegge il motore 1 all'avvio
        if (current_angles[1] < 40.0) {
            current_angles[1] = 40.0;
        }

        // Per sicurezza, allineiamo anche la variabile target iniziale
        if (target_angle_1 < 40.0) {
            target_angle_1 = 40.0;
        }

    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, get_servo_angle_impulse((uint8_t)current_angles[0]));
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_2, get_servo_angle_impulse((uint8_t)current_angles[1]));
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_3, get_servo_angle_impulse((uint8_t)current_angles[2]));
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_4, get_servo_angle_impulse((uint8_t)current_angles[3]));
    HAL_Delay(1000);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
    /* Infinite loop */
      /* USER CODE BEGIN WHILE */
    while (1)
      {
          // 1. CONTROLLO RICEZIONE USB
          if (usb_data_ready) {
              float t0, t1, t2, t3;
              if (sscanf((char*)usb_rx_buffer, "%f,%f,%f,%f", &t0, &t1, &t2, &t3) == 4) {
                  target_angle_0 = t0;
                  target_angle_1 = t1;
                  target_angle_2 = t2;
                  target_angle_3 = t3;
              }
              usb_data_ready = 0;
          }

          // 2. MUOVI IL BRACCIO IN MODO SINCRONIZZATO
          // L'ultimo parametro (1.0) è la "max_speed" in gradi per ciclo.
          // Se vuoi un movimento più lento, metti ad esempio 0.5 o 0.2.
          move_arm_synchronized(&htim4, target_angle_0, target_angle_1, target_angle_2, target_angle_3, 1.0);

          // 3. RITMO (Aggiorna i motori ogni 20 millisecondi = 50 Hz, perfetto per i servi)
          HAL_Delay(20);

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 4;
  RCC_OscInitStruct.PLL.PLLN = 72;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 3;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM3_Init(void)
{

  /* USER CODE BEGIN TIM3_Init 0 */

  /* USER CODE END TIM3_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM3_Init 1 */

  /* USER CODE END TIM3_Init 1 */
  htim3.Instance = TIM3;
  htim3.Init.Prescaler = 16-1;
  htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim3.Init.Period = 20000;
  htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim3) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim3, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim3, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM3_Init 2 */

  /* USER CODE END TIM3_Init 2 */

}

/**
  * @brief TIM4 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM4_Init(void)
{

  /* USER CODE BEGIN TIM4_Init 0 */

  /* USER CODE END TIM4_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM4_Init 1 */

  /* USER CODE END TIM4_Init 1 */
  htim4.Instance = TIM4;
  htim4.Init.Prescaler = 72-1;
  htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim4.Init.Period = 20000;
  htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim4, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim4, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_3) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM4_Init 2 */

  /* USER CODE END TIM4_Init 2 */
  HAL_TIM_MspPostInit(&htim4);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
