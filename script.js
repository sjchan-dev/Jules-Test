document.addEventListener('DOMContentLoaded', () => {
    const listingsContainer = document.querySelector('.listings');
    let allListings = [];

    // Function to render listings
    function renderListings(listings) {
        listingsContainer.innerHTML = ''; // Clear existing listings
        if (!listings) return;
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
    }

    // Fetch and display listings using PapaParse
    Papa.parse('offices.csv', {
        download: true,
        header: true,
        skipEmptyLines: true,
        complete: function(results) {
            allListings = results.data;
            renderListings(allListings);
        },
        error: function(error) {
            console.error('Error parsing CSV:', error);
            listingsContainer.innerHTML = '<p>Error loading listings.</p>';
        }
    });

    // Search functionality
    const searchButton = document.querySelector('.search-bar button');
    const searchInput = document.querySelector('.search-bar input');

    function performSearch() {
        const query = searchInput.value.toLowerCase().trim();
        if (query) {
            const filteredListings = allListings.filter(listing =>
                listing.name.toLowerCase().includes(query)
            );
            renderListings(filteredListings);
        } else {
            renderListings(allListings); // Show all if search is empty
        }
    }

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    });
});
