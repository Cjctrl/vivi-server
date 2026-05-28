# NumPy

NumPy (Numerical Python) is a fundamental package for scientific computing in Python. It provides support for large, multi-dimensional arrays and matrices, along with a collection of mathematical functions to operate on these arrays efficiently.

## Key Features

### N-dimensional Array Object (ndarray)
The core of NumPy is the ndarray object, which is a fast, flexible container for large datasets in Python. Arrays enable you to perform mathematical operations on entire blocks of data using similar syntax to the equivalent operations between scalar elements:

```python
import numpy as np

# Create arrays
a = np.array([1, 2, 3, 4])
b = np.array([2, 3, 4, 5])

# Element-wise operations
print(a * b)  # [2 6 12 20]
print(a + b)  # [3 5 7 9]
```

### Broadcasting
NumPy\'s broadcasting feature allows operations between arrays of different shapes, making it possible to vectorize operations so that loops occur in C instead of Python:

```python
# Add a vector to each row of a matrix
M = np.ones((3, 3))
v = np.array([0, 1, 2])
print(M + v)
# [[1. 2. 3.]
#  [1. 2. 3.]
#  [1. 2. 3.]]
```

### Universal Functions (ufuncs)
NumPy provides fast element-wise operations called universal functions. These are implemented in C for speed and include:
- Mathematical functions (sin, cos, exp, log, etc.)
- Trigonometric functions
- Statistical functions (min, max, mean, std, etc.)
- Logical operations
- Bitwise operations

### Linear Algebra
The numpy.linalg module implements standard linear algebra operations:
- Matrix multiplication (dot product)
- Eigenvalues and eigenvectors
- Singular value decomposition (SVD)
- Matrix inverses
- Determinants
- Solving systems of linear equations

### Fourier Transforms
The numpy.fft module provides functions to compute Fast Fourier Transforms (FFT) and their inverses.

### Random Number Generation
The numpy.random module provides functions for generating random numbers from various probability distributions.

## Array Creation
NumPy offers multiple ways to create arrays:

```python
# From Python lists
arr = np.array([1, 2, 3, 4])

# Arrays of zeros
zeros = np.zeros((3, 4))

# Arrays of ones
ones = np.ones((2, 3, 4), dtype=np.int16)

# Range with uniform spacing
even_numbers = np.arange(0, 10, 2)  # [0 2 4 6 8]

# Linearly spaced numbers
linspace = np.linspace(0, np.pi, 5)  # [0, 0.785, 1.57, 2.356, 3.14]

# Random arrays
random_array = np.random.random((2, 3))  # Uniform distribution [0, 1)
normal_array = np.random.normal(0, 1, (3, 3))  # Normal distribution
```

## Indexing and Slicing
NumPy arrays support flexible indexing and slicing:

```python
# Create a 2D array
x = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# Access elements
print(x[0, 1])  # 2

# Slice rows
print(x[0:2, :])  # First two rows

# Slice columns
print(x[:, 1:3])  # Last two columns

# Integer array indexing
rows = np.array([0, 2])
cols = np.array([1, 2])
print(x[rows, cols])  # [2 9]

# Boolean indexing
print(x[x > 5])  # [6 7 8 9]
```

## Mathematical Operations
NumPy provides a wide range of mathematical operations on arrays:

```python
# Statistical operations
a = np.array([[1, 2, 3], [4, 5, 6]])
print(np.mean(a))       # 3.5
print(np.std(a))        # 1.707...
print(np.median(a))     # 3.5

# Linear algebra
b = np.array([[1, 2], [3, 4]])
print(np.linalg.det(b))  # -2.0
print(np.linalg.inv(b))  # [[-2.   1. ]
                        #  [ 1.5 -0.5]]

# Fourier transform
c = np.array([1, 2, 3, 4])
print(np.fft.fft(c))  # [10.+0.j -2.+2.j -2.+0.j -2.-2.j]
```

## Applications
NumPy is the foundation for many scientific computing libraries in Python:
- SciPy (scientific and technical computing)
- pandas (data manipulation and analysis)
- matplotlib (plotting and visualization)
- scikit-learn (machine learning)
- TensorFlow and PyTorch (deep learning)
- OpenCV (computer vision)
- Astropy (astronomy)
- And many more

## Performance
NumPy arrays are more efficient than Python lists for numerical computations because:
- They are densely packed in memory (homogeneous type)
- Operations are implemented in C, avoiding Python loop overhead
- They support vectorized operations
- Memory layout is cache-friendly

## See Also
- [[SciPy]]
- [[pandas]]
- [[Matplotlib]]
- [[scikit-learn]]
- [[TensorFlow]]
- [[PyTorch]]
- [[Linear algebra]]
- [[Fourier transform]]
- [[Random number generation]]
- [[Array programming]]
