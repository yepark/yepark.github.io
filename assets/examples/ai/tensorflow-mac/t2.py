import tensorflow as tf

tf.random.set_seed(0)
x = tf.random.uniform((100, 1), -1.0, 1.0)
y = 2.0 * x + 1.0 + tf.random.normal((100, 1), stddev=0.05)

w = tf.Variable(0.0)
b = tf.Variable(0.0)
optimizer = tf.keras.optimizers.SGD(learning_rate=0.1)

for step in range(1, 201):
    with tf.GradientTape() as tape:
        pred = w * x + b
        loss = tf.reduce_mean((pred - y) ** 2)
    grads = tape.gradient(loss, [w, b])
    optimizer.apply_gradients(zip(grads, [w, b]))
    if step in (1, 50, 200):
        print(f"step {step:3d}  loss={loss.numpy():.4f}  w={w.numpy():.3f}  b={b.numpy():.3f}")
