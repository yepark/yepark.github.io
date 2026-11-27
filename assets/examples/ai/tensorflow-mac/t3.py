import tensorflow as tf

tf.keras.utils.set_random_seed(42)

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
x_train = x_train.astype("float32") / 255.0
x_test = x_test.astype("float32") / 255.0
print("train:", x_train.shape, "test:", x_test.shape)

model = tf.keras.Sequential([
    tf.keras.Input(shape=(28, 28)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10),
])
model.compile(
    optimizer="adam",
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=["accuracy"],
)
model.summary()

history = model.fit(
    x_train, y_train,
    epochs=5,
    batch_size=64,
    validation_split=0.1,
    callbacks=[tf.keras.callbacks.EarlyStopping(patience=2, restore_best_weights=True)],
    verbose=2,
)

loss, acc = model.evaluate(x_test, y_test, verbose=0)
print(f"test loss={loss:.4f} accuracy={acc:.4f}")

model.save("mnist.keras")
restored = tf.keras.models.load_model("mnist.keras")
logits = restored.predict(x_test[:3], verbose=0)
probs = tf.nn.softmax(logits).numpy()
print("pred:", probs.argmax(axis=1), "label:", y_test[:3], "conf:", probs.max(axis=1).round(3))
