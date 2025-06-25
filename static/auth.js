// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Check if user is already signed in
firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
        console.log('User is signed in:', user);
        // Get the user's token and verify it with the backend
        user.getIdToken().then(token => {
            fetch('/verify-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (!window.location.pathname.includes('/dashboard')) {
                        window.location.href = '/';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.location.href = '/login';
            });
        });
    } else if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
    }
});

// Handle Google sign-in
function signInWithGoogle() {
    const provider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(provider)
        .then((result) => {
            console.log('Google sign-in successful:', result.user);
            result.user.getIdToken().then(token => {
                fetch('/verify-token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ token: token })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = '/';
                    }
                });
            });
        })
        .catch((error) => {
            console.error('Error:', error);
            document.getElementById('error-message').textContent = error.message;
            document.getElementById('error-message').style.display = 'block';
        });
}