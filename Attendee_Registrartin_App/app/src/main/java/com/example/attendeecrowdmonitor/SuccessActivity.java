package com.example.attendeecrowdmonitor; // Keep your package name!

import android.os.Bundle;
import android.widget.Button;
import androidx.activity.EdgeToEdge;
import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

public class SuccessActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 1. Enable modern edge-to-edge display
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_success);

        // 2. Wire up the new Material "Close App" Button
        Button btnFinish = findViewById(R.id.btnFinish);
        if (btnFinish != null) {
            btnFinish.setOnClickListener(v -> {
                // Minimize the app just like the back button does
                moveTaskToBack(true);
            });
        }

        // 3. Handle the Physical Back Button
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                // Moves the app to background to keep the tracking service alive
                moveTaskToBack(true);
            }
        });

        // 4. Adjust padding for system bars (status bar, navigation bar)
        if (findViewById(R.id.main) != null) {
            ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
                Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
                v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
                return insets;
            });
        }
    }
}