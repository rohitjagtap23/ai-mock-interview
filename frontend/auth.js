const SUPABASE_URL = 'https://emnmtzsazhtwvuorpvak.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_RWvhlDZyBEvAaig-NVG1Bw_wgRRlr8g';

const supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);

async function loginUser(email, password) {
    const { data, error } =
        await supabaseClient.auth.signInWithPassword({
            email: email,
            password: password
        });

    return {
        data: data,
        error: error
    };
}

async function signUp(email, password) {
    const { data, error } =
        await supabaseClient.auth.signUp({
            email: email,
            password: password
        });

    return {
        data: data,
        error: error
    };
}

async function getSession() {
    const { data, error } =
        await supabaseClient.auth.getSession();

    return {
        session: data?.session || null,
        error: error
    };
}

async function getCurrentUser() {
    const { data, error } =
        await supabaseClient.auth.getUser();

    if (error) {
        return null;
    }

    return data?.user || null;
}

async function logoutUser() {
    const { error } =
        await supabaseClient.auth.signOut();

    if (error) {
        alert("Logout failed: " + error.message);
        return false;
    }

    localStorage.clear();
    sessionStorage.clear();

    window.location.href = "login.html";

    return true;
}

function logout() {
    return logoutUser();
}

async function saveProfile(profile) {
    const user = await getCurrentUser();

    if (!user) {
        return {
            error: {
                message: "User is not logged in."
            }
        };
    }

    return await supabaseClient
        .from("users")
        .upsert({
            id: user.id,
            email: user.email,
            name: profile.name || "",
            target_role: profile.target_role || "",
            location: profile.location || "",
            experience_level:
                profile.experience_level || "Beginner",
            skills: profile.skills || []
        });
}

async function getUserProfile() {
    const user = await getCurrentUser();

    if (!user) {
        return null;
    }

    const { data, error } =
        await supabaseClient
            .from("users")
            .select("*")
            .eq("id", user.id)
            .single();

    if (error) {
        console.error(error);
        return null;
    }

    return data;
}

document.addEventListener("DOMContentLoaded", function () {

    const buttons = document.querySelectorAll(
        "#logoutButton, #logoutBtn, .logout-button, .logout-btn"
    );

    buttons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            event.preventDefault();

            logoutUser();

        });

    });

});