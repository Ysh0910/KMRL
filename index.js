const express = require('express');
const app = express();
const port = 3000;
const path = require('path');
var methodOverride = require('method-override');
const axios = require('axios');
const session = require('express-session');

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(methodOverride('_method'));

// Session middleware setup
app.use(session({
    secret: 'your-very-secret-key-change-it', // <-- IMPORTANT: Change this to a random secret string
    resave: false,
    saveUninitialized: false,
    cookie: { 
        secure: false, // Set to true if you're using HTTPS
        httpOnly: true 
    }
}));

// API base URL
const API_BASE_URL = 'http://localhost:8000';

// Middleware to check if the user is authenticated
const isAuthenticated = (req, res, next) => {
    if (req.session.accessToken) {
        return next();
    }
    res.redirect('/login');
};

app.get('/', (req,res)=> {
    res.render('index.ejs');
});

app.get("/login", (req, res) => {
    const error = req.session.error;
    const success = req.session.success;
    req.session.error = null; // Clear messages after displaying
    req.session.success = null;
    res.render("login.ejs", { error, success });
});

app.get("/signup", (req, res) => {
    const error = req.session.error;
    const success = req.session.success;
    req.session.error = null;
    req.session.success = null;
    res.render("signup.ejs", { error, success });
});

// Login POST route
app.post("/login", async (req, res) => {
    try {
        const { email, password, remember } = req.body;
        
        // 1. Get tokens from the API
        const tokenResponse = await axios.post(`${API_BASE_URL}/auth/jwt/create/`, {
            email: email,
            password: password
        });

        if (tokenResponse.data.access && tokenResponse.data.refresh) {
            // Store tokens in session
            req.session.accessToken = tokenResponse.data.access;
            req.session.refreshToken = tokenResponse.data.refresh;
            
            // 2. Get user details using the access token
            const userResponse = await axios.get(`${API_BASE_URL}/auth/users/me/`, {
                headers: {
                    'Authorization': `JWT ${req.session.accessToken}`
                }
            });

            // Store user info in session
            req.session.user = userResponse.data;
            
            if (remember) {
                req.session.cookie.maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
            }
            
            res.redirect('/dashboard');
        } else {
            req.session.error = 'Invalid credentials';
            res.redirect('/login');
        }
    } catch (error) {
        console.error('Login error:', error.response?.data || error.message);
        req.session.error = 'Invalid email or password.';
        res.redirect('/login');
    }
});

// Signup POST route
app.post("/signup", async (req, res) => {
    try {
        const { userid, email, password, role } = req.body;
        
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        if (!passwordRegex.test(password)) {
            req.session.error = 'Password must be at least 8 characters with uppercase, lowercase, and number.';
            return res.redirect('/signup');
        }
        
        // The API expects 'name' and 're_password'
        const response = await axios.post(`${API_BASE_URL}/auth/users/`, {
            email: email,
            name: userid, // Map userid from form to name for API
            password: password,
            re_password: password
        });

        if (response.status === 201) {
            req.session.success = 'Account created successfully! Please log in.';
            res.redirect('/login');
        } else {
            req.session.error = 'Failed to create account. Please try again.';
            res.redirect('/signup');
        }
    } catch (error) {
        console.error('Signup error:', error.response?.data || error.message);
        let errorMessage = 'An unexpected error occurred.';
        
        if (error.response?.data) {
            const errors = error.response.data;
            if (errors.email) {
                errorMessage = 'This email already exists or is invalid.';
            } else if (errors.name) {
                errorMessage = 'This User ID already exists.';
            } else if (errors.password) {
                errorMessage = 'Password requirements not met. Please check the criteria.';
            }
        }
        
        req.session.error = errorMessage;
        res.redirect('/signup');
    }
});

// Logout route
app.post("/logout", (req, res) => {
    req.session.destroy((err) => {
        if (err) {
            console.error('Logout error:', err);
            return res.redirect('/dashboard'); // Or show an error page
        }
        res.redirect('/login');
    });
});

// Password reset request
app.post("/forgot-password", async (req, res) => {
    try {
        await axios.post(`${API_BASE_URL}/auth/users/reset_password/`, {
            email: req.body.email
        });
        
        req.session.success = 'If an account with that email exists, a password reset link has been sent.';
        res.redirect('/login');
    } catch (error) {
        console.error('Password reset error:', error.response?.data || error.message);
        req.session.error = 'Failed to send password reset email.';
        res.redirect('/login');
    }
});

// === Protected Routes ===

// Apply the isAuthenticated middleware to all routes that require a login
app.get('/dashboard', isAuthenticated, (req,res)=> {
    Promise.all([
        axios.get(`${API_BASE_URL}/fitness_certificates/`),
        axios.get(`${API_BASE_URL}/branding/`),
        axios.get(`${API_BASE_URL}/mileage/`)
    ])
    .then(([fitnessResponse, brandingResponse, mileageResponse]) => {
        res.render('dashboard.ejs', { 
            user: req.session.user, // Pass user info to the template
            fitnessCertificates: fitnessResponse.data,
            brandingData: brandingResponse.data,
            mileage: mileageResponse.data
        });
    })
    .catch(error => {
        console.error('Error fetching dashboard data:', error.message);
        res.render('dashboard.ejs', { 
            user: req.session.user,
            fitnessCertificates: [],
            brandingData: [],
            mileage: []
        });
    });
});

app.get('/trains', isAuthenticated, (req, res) => {
    Promise.all([
        axios.get(`${API_BASE_URL}/mileage/`),
        axios.get(`${API_BASE_URL}/branding/`)
    ])
    .then(([mileageResponse, brandingResponse]) => {
        const sortedMileage = mileageResponse.data.sort((a, b) => a.train.localeCompare(b.train));
        const sortedBranding = brandingResponse.data.sort((a, b) => a.train.localeCompare(b.train));
        
        res.render('trains.ejs', { 
            user: req.session.user,
            mileage: sortedMileage,
            brandingData: sortedBranding,
            selectedTrain: sortedMileage[0]?.train || null
        });
    })
    .catch(error => {
        console.error('Error fetching trains data:', error.message);
        res.render('trains.ejs', { 
            user: req.session.user,
            mileage: [],
            brandingData: [],
            selectedTrain: null
        });
    });
});

// Add other protected routes here...
app.get('/reports', isAuthenticated, (req, res) => {
    res.render('reports.ejs', { user: req.session.user });
});
app.get('/settings', isAuthenticated, (req, res) => {
    res.render('settings.ejs', { user: req.session.user });
});
app.get('/service', isAuthenticated,  (req, res) => {
    res.render('service.ejs', { user: req.session.user });
});

app.get('/standby', isAuthenticated, (req, res) => {
    res.render('standby.ejs', { user: req.session.user });
});

app.get('/fitness', isAuthenticated, (req, res) => {
    res.render('fitness.ejs', { user: req.session.user });
});

app.get("/maintenance",  (req, res) => {
        axios.get(`${API_BASE_URL}/joboards/`)
            .then(response => {
                res.render("maintenance.ejs", { jobCards: response.data });
            })
            .catch(error => {
                console.error('Error fetching job cards:', error.message);
                res.render("maintenance.ejs", { jobCards: [] });
            });
});

app.get('/alerts', isAuthenticated, (req, res) => {
    res.render('alerts.ejs', { user: req.session.user });
});

app.get("/schedule", (req, res) => {
        // Example: Fetch predictions using dummy payload (replace with real data integration as needed)
        axios.post(`${API_BASE_URL}/getpredictions/`, {})
            .then(response => {
                res.render("schedule.ejs", { predictions: response.data });
            })
            .catch(error => {
                console.error('Error fetching predictions:', error.message);
                res.render("schedule.ejs", { predictions: {} });
            });
});


app.get('/staff', isAuthenticated, (req, res) => {
    res.render('staff.ejs', { user: req.session.user });
});


// Start the server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});