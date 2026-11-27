import tensorflow as tf

print("TensorFlow", tf.__version__)
print("devices:", [d.device_type for d in tf.config.list_physical_devices()])

a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
b = tf.constant([[1.0], [1.0]])
print("a.shape:", a.shape, "dtype:", a.dtype.name)
print("a @ b:", (a @ b).numpy().ravel())
print("a * 10:", (a * 10).numpy().tolist())
print("row mean:", tf.reduce_mean(a, axis=1).numpy())
