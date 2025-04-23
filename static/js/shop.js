const products = [
  {
    id: 1,
    name: 'Café Especial Premium',
    price: 49.90,
    category: 'coffee',
    image: '../img/Coffee product.png',
    description: 'Blend exclusivo de grãos selecionados'
  },
  {
    id: 2,
    name: 'Café Gourmet',
    price: 39.90,
    category: 'coffee',
    image: '../img/Coffee product.png',
    description: 'Café gourmet torrado artesanalmente'
  },
  {
    id: 3,
    name: 'Prensa Francesa',
    price: 129.90,
    category: 'equipment',
    image: '../img/copo cafee.png',
    description: 'Prensa francesa em aço inoxidável'
  },
  {
    id: 4,
    name: 'Moedor Manual',
    price: 89.90,
    category: 'equipment',
    image: '../img/Coffee product.png',
    description: 'Moedor manual de café ajustável'
  },
  {
    id: 5,
    name: 'Caneca Térmica',
    price: 59.90,
    category: 'accessories',
    image: '../img/copo cafee.png',
    description: 'Caneca térmica de 500ml'
  },
  {
    id: 6,
    name: 'Kit Barista',
    price: 199.90,
    category: 'accessories',
    image: '../img/Coffee product.png',
    description: 'Kit completo para barista iniciante'
  }
];

// Cart state
let cart = [];

// DOM Elements
const productsGrid = document.getElementById('productsGrid');
const cartModal = document.getElementById('cartModal');
const cartItems = document.getElementById('cartItems');
const cartTotal = document.getElementById('cartTotal');
const cartCount = document.querySelector('.cart-count');
const menuBtn = document.getElementById('menuBtn');
const navLinks = document.getElementById('navLinks');

// Mobile menu functionality
menuBtn.addEventListener('click', () => {
  navLinks.classList.toggle('active');
});

// Filter functionality
document.querySelectorAll('.filter-btn').forEach(button => {
  button.addEventListener('click', () => {
    const category = button.dataset.category;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    button.classList.add('active');
    
    // Filter products
    displayProducts(category);
  });
});

// Display products
function displayProducts(category = 'all') {
  const filteredProducts = category === 'all' 
    ? products 
    : products.filter(product => product.category === category);

  productsGrid.innerHTML = filteredProducts.map(product => `
    <div class="product-card">
      <div class="product-image">
        <img src="${product.image}" alt="${product.name}">
      </div>
      <div class="product-info">
        <h3>${product.name}</h3>
        <p>${product.description}</p>
        <div class="product-price">R$ ${product.price.toFixed(2)}</div>
        <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
          Adicionar ao Carrinho
        </button>
      </div>
    </div>
  `).join('');
}

// Cart functionality
window.addToCart = (productId) => {
  const product = products.find(p => p.id === productId);
  const cartItem = cart.find(item => item.id === productId);
  
  if (cartItem) {
    cartItem.quantity++;
  } else {
    cart.push({ ...product, quantity: 1 });
  }
  
  updateCart();
};

function updateCart() {
  // Update cart count
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
  cartCount.textContent = totalItems;
  
  // Update cart items
  cartItems.innerHTML = cart.map(item => `
    <div class="cart-item">
      <img src="${item.image}" alt="${item.name}">
      <div class="cart-item-info">
        <h4>${item.name}</h4>
        <p>R$ ${item.price.toFixed(2)}</p>
        <div class="cart-item-quantity">
          <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
          <span>${item.quantity}</span>
          <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
        </div>
      </div>
    </div>
  `).join('');
  
  // Update total
  const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  cartTotal.textContent = `R$ ${total.toFixed(2)}`;
}

window.updateQuantity = (productId, newQuantity) => {
  if (newQuantity < 1) {
    cart = cart.filter(item => item.id !== productId);
  } else {
    const item = cart.find(item => item.id === productId);
    if (item) {
      item.quantity = newQuantity;
    }
  }
  
  updateCart();
};

// Cart modal
document.getElementById('cartButton').addEventListener('click', (e) => {
  e.preventDefault();
  cartModal.style.display = 'block';
});

document.querySelector('.close-btn').addEventListener('click', () => {
  cartModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
  if (e.target === cartModal) {
    cartModal.style.display = 'none';
  }
});

// Clear cart
document.querySelector('.clear-cart-btn').addEventListener('click', () => {
  cart = [];
  updateCart();
});

// Checkout
document.querySelector('.checkout-btn').addEventListener('click', () => {
  if (cart.length === 0) {
    alert('Seu carrinho está vazio!');
    return;
  }
  
  alert('Compra finalizada com sucesso!');
  cart = [];
  updateCart();
  cartModal.style.display = 'none';
});

// Initialize products display
displayProducts();