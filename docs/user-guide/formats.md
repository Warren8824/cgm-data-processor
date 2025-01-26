<div class="hero">
  <h1>Supported File Formats</h1>
  <p>Supported diabetes device data formats</p>
</div>

## 📱 XDrip+ SQLite

<div class="feature-card">
<ul>
    <li>Default SQLite database from XDrip+</li>
    <li>Contains BgReadings and Treatments tables</li>
    <li>Full CGM and treatment data support</li>
    <li>Export: Settings → Data Export → Export Database</li>
</ul>
</div>

## 📑 Schema Structure

<div class="feature-card">

```sql
-- BgReadings Table
timestamp          -- UTC timestamp
calculated_value   -- Glucose in mg/dL
raw_data          -- Raw sensor data

-- Treatments Table
timestamp    -- UTC timestamp
insulin      -- Insulin dose in units
insulinJSON  -- Insulin type metadata
carbs       -- Carbohydrates in grams
notes       -- Treatment notes
```

</div>

## 🔄 Other Formats (Coming Soon)

<div class="feature-card">
<ul>
    <li>Dexcom CSV Export</li>
    <li>Freestyle Libre CSV</li>
    <li>Nightscout Data</li>
</ul>
</div>

## Add Custom File Formats

Check out our API and developer guide if you would like to add your own formats to the program.