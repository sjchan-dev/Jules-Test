
document.addEventListener('DOMContentLoaded', () => {
    const listings = [
        {
            name: 'Modern Office Space',
            price: '$1,000/month',
            image: 'https://via.placeholder.com/300'
        },
        {
            name: 'Creative Loft',
            price: '$1,500/month',
            image: 'https://via.placeholder.com/300'
        },
        {
            name: 'Corporate Suite',
            price: '$2,000/month',
            image: 'https://via.placeholder.com/300'
        }
    ];

    const listingsContainer = document.querySelector('.listings');

    listings.forEach(listing => {
        const listingElement = document.createElement('div');
        listingElement.classList.add('listing');
        listingElement.innerHTML = `
            <img src="${listing.image}" alt="${listing.name}">
            <h3>${listing.name}</h3>
            <p>${listing.price}</p>
        `;
        listingsContainer.appendChild(listingElement);
    });
});
