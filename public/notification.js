// Este archivo contiene funciones para manejar las notificaciones de audio
// Puedes incluirlo en tu proyecto o añadir este código directamente en principal.html

// Función para precargar el sonido de notificación
let notificationSound = null

function preloadNotificationSound() {
  try {
    notificationSound = new Audio("/static/sound/notification.mp3")
    // Precargar el audio
    notificationSound.load()
    console.log("Sonido de notificación precargado correctamente")
  } catch (e) {
    console.error("Error al precargar el sonido de notificación:", e)
  }
}

// Función para reproducir el sonido de notificación
function playNotificationSound() {
  try {
    if (notificationSound) {
      // Reiniciar el audio para poder reproducirlo múltiples veces
      notificationSound.currentTime = 0

      // Reproducir con manejo de promesa (para navegadores modernos)
      const playPromise = notificationSound.play()

      if (playPromise !== undefined) {
        playPromise
          .then((_) => {
            console.log("Reproducción de sonido iniciada correctamente")
          })
          .catch((error) => {
            console.error("Error al reproducir el sonido:", error)
            // Intentar reproducir después de una interacción del usuario
            document.addEventListener(
              "click",
              function audioUnlock() {
                notificationSound.play()
                document.removeEventListener("click", audioUnlock)
              },
              { once: true },
            )
          })
      }
    } else {
      // Si el sonido no se precargó, intentar reproducirlo directamente
      const audio = new Audio("/static/sound/notification.mp3")
      audio.play().catch((e) => console.error("Error al reproducir sonido:", e))
    }
  } catch (e) {
    console.error("Error al reproducir el sonido de notificación:", e)
  }
}

// Precargar el sonido cuando se carga la página
document.addEventListener("DOMContentLoaded", preloadNotificationSound)

