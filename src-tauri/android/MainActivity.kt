package studio.nebula.ascii

import android.graphics.Color
import android.os.Bundle
import android.view.View
import androidx.activity.SystemBarStyle
import androidx.activity.enableEdgeToEdge
import androidx.core.graphics.Insets
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

class MainActivity : TauriActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val barStyle = SystemBarStyle.dark(Color.TRANSPARENT)
        enableEdgeToEdge(statusBarStyle = barStyle, navigationBarStyle = barStyle)
        super.onCreate(savedInstanceState)

        val content = findViewById<View>(android.R.id.content)
        content.setBackgroundColor(Color.rgb(20, 21, 26))
        val safeTypes = WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
        ViewCompat.setOnApplyWindowInsetsListener(content) { view, insets ->
            val safe = insets.getInsets(safeTypes)
            view.setPadding(safe.left, safe.top, safe.right, safe.bottom)
            // The native container already applied these insets. Keep IME updates
            // flowing to the WebView and avoid applying the system bars twice.
            WindowInsetsCompat.Builder(insets)
                .setInsets(safeTypes, Insets.NONE)
                .build()
        }
        ViewCompat.requestApplyInsets(content)
    }
}
