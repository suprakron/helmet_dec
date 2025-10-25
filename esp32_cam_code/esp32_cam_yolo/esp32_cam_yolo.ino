#include "esp_camera.h"
#include "board_config.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ---------------- WiFi ----------------
const char* ssid = "iPhonemap’s";       
const char* password = "gA4sbovwhc";

// ---------------- Django API URL ----------------
const char* serverName = "http://172.20.10.5:8000/api/upload_image/"; 

void setup() {
  Serial.begin(115200);
  Serial.println();

  // Connect WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  int retry_count = 0;
  while (WiFi.status() != WL_CONNECTED && retry_count < 20) {
    delay(500);
    Serial.print(".");
    retry_count++;
  }
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("\n❌ WiFi connection failed");
    return;
  }
  Serial.println("\n✅ WiFi connected!");
  Serial.print("ESP32-CAM IP Address: ");
  Serial.println(WiFi.localIP());

  // Camera configuration
  camera_config_t config;
  memset(&config, 0, sizeof(camera_config_t)); 
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_SVGA; // 800x600
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_VGA; // 640x480
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Camera init failed!");
    while(true);
  }
}

void loop() {
  // ตรวจสอบ WiFi
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("⚠️ WiFi Disconnected, reconnecting...");
    int retry = 0;
    while(WiFi.status() != WL_CONNECTED && retry < 10){
      WiFi.reconnect();
      delay(1000);
      retry++;
    }
    if(WiFi.status() != WL_CONNECTED){
      Serial.println("❌ WiFi reconnect failed, skip this loop");
      return;
    }
  }

  // Capture image
  camera_fb_t * fb = esp_camera_fb_get();
  if(!fb){
    Serial.println("❌ Camera capture failed");
    return;
  }

  // ส่งภาพไป Django API
  HTTPClient http;
  http.begin(serverName);
  http.setTimeout(10000); // 10 วินาที
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("User-Agent", "ESP32-CAM");

  int httpResponseCode = http.POST(fb->buf, fb->len);
  if(httpResponseCode > 0){
    Serial.printf("✅ HTTP Response code: %d\n", httpResponseCode);
    String payload = http.getString();
    Serial.println("Server Response: " + payload);
  } else {
    Serial.printf("❌ Error sending image. Code: %d\n", httpResponseCode);
  }

  http.end();
  esp_camera_fb_return(fb);
 
  delay(5000);  
}
