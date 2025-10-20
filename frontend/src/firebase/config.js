// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDztj2xRxvLGXeBG0E1wODkEnJJ1Rk2sh4",
  authDomain: "vernacular-voice-bot.firebaseapp.com",
  projectId: "vernacular-voice-bot",
  storageBucket: "vernacular-voice-bot.firebasestorage.app",
  messagingSenderId: "239176443801",
  appId: "1:239176443801:web:6dd30e0b4753a3f16e9508"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);