package com.example.managercrowdmonitor;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.toolbox.JsonArrayRequest;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {
    // Renamed variables to match the Manager model logic
    private EditText etManagerName, etMobile, etEmail, etManagerRole;
    private Spinner spinnerEvents;
    private RequestQueue requestQueue;

    private List<String> eventNames = new ArrayList<>();
    private List<String> eventIds = new ArrayList<>();

    // Ensure this URL is always updated if Ngrok restarts
    private final String BASE_URL = "https://southbound-earle-pressuringly.ngrok-free.dev/api/";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize UI components using your existing XML layout IDs
        etManagerName = findViewById(R.id.etName);
        etMobile = findViewById(R.id.etMobile);
        etEmail = findViewById(R.id.etEmail);

        // Repurposing the old 'accompanies' field to act as the 'manager_role' input
        etManagerRole = findViewById(R.id.etAccompanies);

        spinnerEvents = findViewById(R.id.spinnerEvents);

        requestQueue = Volley.newRequestQueue(this);

        // Fetch dynamic event list from Django
        fetchEvents();

        findViewById(R.id.btnRegister).setOnClickListener(v -> checkPermissionsAndRegister());
    }

    private void fetchEvents() {
        JsonArrayRequest request = new JsonArrayRequest(Request.Method.GET, BASE_URL + "get-events/", null,
                response -> {
                    try {
                        eventNames.clear();
                        eventIds.clear();
                        for (int i = 0; i < response.length(); i++) {
                            JSONObject obj = response.getJSONObject(i);
                            eventNames.add(obj.getString("event_name"));
                            eventIds.add(obj.getString("id"));
                        }
                        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                                android.R.layout.simple_spinner_item, eventNames);
                        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                        spinnerEvents.setAdapter(adapter);
                    } catch (JSONException e) { e.printStackTrace(); }
                },
                error -> Toast.makeText(this, "Could not load events. Check Ngrok & Django!", Toast.LENGTH_LONG).show()
        );
        requestQueue.add(request);
    }

    private void checkPermissionsAndRegister() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, 101);
        } else {
            sendRegistrationData();
        }
    }

    private void sendRegistrationData() {
        int selectedPosition = spinnerEvents.getSelectedItemPosition();
        if (selectedPosition == Spinner.INVALID_POSITION) {
            Toast.makeText(this, "Please select an event first", Toast.LENGTH_SHORT).show();
            return;
        }

        JSONObject postData = new JSONObject();
        try {
            // Updated keys to match what your Manager Django view will likely expect
            postData.put("event_id", eventIds.get(selectedPosition));
            postData.put("manager_name", etManagerName.getText().toString());
            postData.put("manager_role", etManagerRole.getText().toString());
            postData.put("mobile_no", etMobile.getText().toString());
            postData.put("email_id", etEmail.getText().toString());
        } catch (JSONException e) { e.printStackTrace(); }

        // Updated the endpoint to hit the manager registration URL
        JsonObjectRequest request = new JsonObjectRequest(Request.Method.POST, BASE_URL + "register-manager/", postData,
                response -> {
                    try {
                        // Extracting manager_id instead of attendee_id
                        String managerId = response.getString("manager_id");

                        // 1. Start the Background Service
                        startBackgroundTracking(managerId);

                        // 2. TRIGGER THE SUCCESS SCREEN
                        Intent intent = new Intent(MainActivity.this, SuccessActivity.class);
                        startActivity(intent);

                        // 3. Optional: Close this form so they can't go back to it
                        finish();

                    } catch (JSONException e) {
                        e.printStackTrace();
                        Toast.makeText(this, "Server Response Error!", Toast.LENGTH_SHORT).show();
                    }
                },
                error -> Toast.makeText(this, "Registration Failed! Check your internet/Ngrok.", Toast.LENGTH_SHORT).show()
        );
        requestQueue.add(request);
    }

    private void startBackgroundTracking(String managerId) {
        Intent intent = new Intent(this, LocationService.class);
        // Passing MANAGER_ID to the location service
        intent.putExtra("MANAGER_ID", managerId);
        startForegroundService(intent);
        Toast.makeText(this, "Manager Tracking Activated!", Toast.LENGTH_LONG).show();
    }
}