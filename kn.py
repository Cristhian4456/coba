# Import libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
import numpy as np

# Fungsi untuk memuat dataset dari CSV
def load_custom_dataset(file_path):
    dataset = pd.read_csv(file_path)  # Membaca dataset dari file CSV
    X = dataset.iloc[:, :-1].values   # Fitur (semua kolom kecuali kolom terakhir)
    y = dataset.iloc[:, -1].values    # Label (kolom terakhir)
    print("Label data:", y)
    return X, y

# Fungsi untuk membagi dataset menjadi data training dan testing
def split_data(X, y, test_size=0.3, random_state=42):
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

# Fungsi untuk melatih model K-NN
def train_knn(X_train, y_train, n_neighbors=3):
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)  # Inisialisasi model K-NN
    knn.fit(X_train, y_train)  # Melatih model
    return knn

# Fungsi untuk melakukan prediksi dan evaluasi
def predict_and_evaluate(knn, X_test, y_test):
    y_pred = knn.predict(X_test)
    accuracy = knn.score(X_test, y_test)
    print("Hasil prediksi:", y_pred)
    print("Label sebenarnya:", y_test)
    print(f"Akurasi model: {accuracy*100:.2f}%")
    return y_pred, accuracy

# Fungsi untuk menambah data baru ke dataset
def add_new_data(X_train, y_train, new_data, new_label):
    X_train = np.vstack([X_train, new_data])  # Tambah data baru ke dataset fitur
    y_train = np.append(y_train, new_label)   # Tambah label data baru
    return X_train, y_train

# Fungsi untuk prediksi data baru
def predict_new_data(knn, new_data):
    pred_new = knn.predict(new_data)
    return pred_new

# Fungsi untuk menghitung K-NN pada tiga data dan memilih prediksi berdasarkan nilai terkecil
def predict_three_new_data(knn, new_data_list):
    distances = []
    for new_data in new_data_list:
        distance, index = knn.kneighbors(new_data, return_distance=True)  # Dapatkan jarak terdekat
        avg_distance = np.mean(distance)  # Hitung rata-rata jarak K-NN untuk data ini
        prediction = knn.predict(new_data)  # Prediksi label untuk data ini
        distances.append((avg_distance, prediction[0]))
    
    # Sortir berdasarkan jarak terkecil dan ambil prediksi dengan jarak terdekat
    distances = sorted(distances, key=lambda x: x[0])
    print("Jarak dan prediksi untuk tiga data baru:")
    for dist, pred in distances:
        print(f"Jarak: {dist}, Prediksi: {pred}")
    
    # Pilih prediksi dengan jarak terdekat
    return distances[0][1]

# Main program
if __name__ == "__main__":
    # Langkah 1: Memuat dataset dari file CSV
    file_path = r"D:\Sekolah\TTU 1\New folder/load1.csv"  # Ganti dengan path file CSV kamu
    X, y = load_custom_dataset(file_path)

    # Langkah 2: Membagi dataset menjadi data training dan testing
    X_train, X_test, y_train, y_test = split_data(X, y)
    print("ini data", X_test)

    # Langkah 3: Melatih model K-NN
    knn_model = train_knn(X_train, y_train)

    # Langkah 4: Prediksi dan evaluasi model
    predict_and_evaluate(knn_model, X_test, y_test)

    # Langkah 5: Tambah tiga data baru dan prediksi ulang
    new_data_list = [
        np.array([[0, 0, 0]]),  # Contoh data baru pertama (sesuaikan dengan dataset)
        np.array([[2, 0, 0]]),  # Contoh data baru kedua
        np.array([[0, 0, 0]])   # Contoh data baru ketiga
    ]

    # Langkah 6: Prediksi tiga data baru dan pilih prediksi dengan jarak terdekat
    final_prediction = predict_three_new_data(knn_model, new_data_list)
    print(f"Prediksi akhir berdasarkan tiga data baru: {final_prediction}")

    # Langkah 7: Update dataset dengan data baru dan latih ulang model (optional)
    # Kamu bisa pilih salah satu dari tiga data baru untuk ditambahkan
    X_train, y_train = add_new_data(X_train, y_train, new_data_list[0], final_prediction)
    knn_model = train_knn(X_train, y_train)
    print(X_train)
    print(y_train)
    # Langkah 8: Prediksi ulang setelah update dataset
    predict_and_evaluate(knn_model, X_test, y_test)
