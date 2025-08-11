# Vahan Vehicle Registration Analytics Dashboard 🚗📊

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37.0-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.2.2-blueviolet.svg)

An end-to-end data engineering project that automates the collection, processing, and visualization of vehicle registration data from India's Vahan Parivahan portal. The final output is a sophisticated, interactive web dashboard built with Streamlit.


---

## 🚀 Project Overview

This project demonstrates a complete three-stage data pipeline for turning raw, messy web data into actionable insights.

1.  **Automated Data Fetching**: A robust Selenium script (`fetch_vahan.py`) navigates the official Vahan dashboard, handles dynamic web elements, and downloads the latest registration data by "Maker" and "Vehicle Category".
2.  **Production-Grade Data Processing**: A powerful script (`process_registrations.py`) reads messy, multi-level header Excel files, cleans them, transforms the data from wide to tidy format, and combines them into a single, analysis-ready CSV file.
3.  **Interactive Analytics Dashboard**: A professional Streamlit application (`app.py`) that allows users to dynamically filter and explore the data with beautiful, interactive charts and KPIs powered by Plotly.

![Project Workflow](https://placehold.co/800x250/0E1117/FFFFFF?text=Fetch%20Data%20%E2%9E%A1%20Process%20Data%20%E2%9E%A1%20Visualize%20Dashboard&font=roboto)

## 🛠️ Tech Stack

| Component           | Technology                            |
| ------------------- | ------------------------------------- |
| **Data Fetching** | `Python`, `Selenium`, `webdriver-manager` |
| **Data Processing** | `Python`, `Pandas`                      |
| **Dashboard** | `Streamlit`, `Plotly`                   |

## 📈 Key Dashboard Features

* **Dynamic Filtering**: Analyze data by "Maker" or "Vehicle Category", select the Top N performers, and search for specific entities.
* **Rich Visualizations**: Includes bar charts, donut charts, treemaps, histograms, and box plots for a comprehensive view.
* **Data Explorer**: An interactive table allows for easy sorting, searching, and downloading of the filtered data as a CSV.
* **Polished UI**: Custom CSS is used to create a professional and visually appealing dark-themed dashboard.

## ▶️ Getting Started

To run this project locally, ensure you have Python 3.9+ installed and follow these steps.

### 1. Clone the Repository

```sh
git clone [https://github.com/your-username/Vahan-Analysis.git](https://github.com/your-username/Vahan-Analysis.git)
cd Vahan-Analysis
```

### 2. Install Dependencies

Install all the required Python packages using the `requirements.txt` file.

```sh
pip install -r requirements.txt
```

### 3. Run the Pipeline

Execute the scripts in the following order to fetch, process, and visualize the data.

**Step 1: Fetch the Raw Data**

This script will open a Chrome browser, download the data, and place it in the `data/raw/` folder.

```sh
python fetch_vahan.py
```

**Step 2: Process the Raw Data**

This script will clean the downloaded files and create the final `vahan_processed_tidy.csv` file in the `data/processed/` directory.

```sh
python process_registrations.py
```

**Step 3: Launch the Analytics Dashboard**

Finally, launch the Streamlit web application.

```sh
streamlit run app.py
```

Your web browser will automatically open a new tab with the interactive dashboard.

## 📂 Repository Structure

```
Vahan-Analysis/
│
├── 📂 data/
│   ├── 📂 raw/              # Raw .xlsx files are downloaded here
│   └── 📂 processed/        # Cleaned vahan_processed_tidy.csv is saved here
│
├── 📜 app.py               # The main Streamlit dashboard application
├── 📜 fetch_vahan.py      # Selenium script to download data
├── 📜 process_registrations.py # Script to clean and process raw data
├── 📜 requirements.txt    # Project dependencies
└── 📜 README.md            # You are here!
```

## 🤝 Contributing

Contributions are welcome! If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Contact

Sahil Awasarkar - [sahilawasarkar142@gmail.com](mailto:sahilawasarkar142@gmail.com)

Project Link: [https://github.com/AwasarkarSahil/Vahan-Analysis](https://github.com/AwasarkarSahil/Vahan-Analysis)
