import React, { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/router';


export default function Home() {
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
    mfa_code: '',
  });
  const [passwordShown, setPasswordShown] = useState(false);

  const router = useRouter();

  const handleChange = (e) => {
    setLoginData({ ...loginData, [e.target.name]: e.target.value });
  };

  const generateRandomString = () => {
    const randomNumber = Math.floor(Math.random() * 10000);
    return randomNumber.toString().padStart(4, '0');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Concatenate a random string with user email
    const user_token = loginData.email + generateRandomString();

    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/login', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: loginData.email,
          password: loginData.password,
          mfa_code: loginData.mfa_code,
          user_token: user_token,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Handle successful login here. Possibly redirect or set some auth state.
        console.log('Login successful:', data);
        sessionStorage.setItem('userToken', user_token);
        router.push('/analysisinput');
      } else {
        // Handle errors, for example, show an error message to the user
        console.log('Login failed:', data.message);
        window.alert('Login Failed: ' + data.message);
      }
    } catch (error) {
      // Catch network errors or issues with the fetch call
      console.error('There was an error with the login request:', error);
      window.alert('There was an error with the login request: ' + error);
    }
  };
  


  const togglePasswordVisibility = () => {
    setPasswordShown(!passwordShown);
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-black text-white">
      {/* Left Side */}
      <div className="md:w-1/2 flex flex-col justify-center p-12 space-y-6">
        <h1 className="text-5xl font-bold">Realized Returns Summary</h1>
        <p className="text-xl">
          Unlock the power of your Robinhood trading data with our intuitive web app. Easily log in with your Robinhood credentials to access a comprehensive summary of your realized and unrealized gains and losses.
        </p>
        <div className="space-y-1">
          <p className="text-xl font-bold">Key Features:</p>
          <ul className="text-xl list-disc list-inside">
            <li>Instant access to your returns summary</li>
            <li>Customizable analysis periods</li>
            <li>Support for stocks, ETFs, and crypto</li>
          </ul>
        </div>
        <div className="space-y-1">
          <p className="text-xl font-bold">Benefits:</p>
          <ul className="text-xl list-disc list-inside">
            <li>Gain valuable investment insights</li>
            <li>Simplify tax loss harvesting</li>
            <li>Save time with automated calculations</li>
          </ul>
        </div>
        <p className="text-xl">
          Log in now and take control of your Robinhood data today!
        </p>
        <div className="mt-auto space-y-2">
          <p className="g italic">
            This app is not affiliated with or endorsed by Robinhood Markets Inc.
          </p>
          <p className="g italic">
            Your privacy is our priority. We never store your credentials or data, and all information is securely erased after each session.
          </p>
          <p className="g italic">
            View our <a href="https://github.com/chakshu-agarwal/returnssummary" target="_blank" rel="noopener noreferrer" className="text-blue-500">code repository</a> to verify its safety and security, and provide feedback on how we can improve it further.
          </p>
        </div>
      </div>

      {/* Right Side */}
      <div className="flex-1 flex items-center justify-center">
        <div className="bg-white text-black w-full max-w-md mx-auto p-8 rounded-lg">
          <h2 className="text-3xl font-bold mb-10">Log in to Robinhood</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="text-sm font-bold">Email</label>
              <input
                type="text"
                name="email"
                id="email"
                value={loginData.email}
                onChange={handleChange}
                className="w-full p-2 mt-1 rounded-md border border-gray-300"
                required
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="text-sm font-bold">Password</label>
              <input
                type={passwordShown ? 'text' : 'password'}
                name="password"
                id="password"
                value={loginData.password}
                onChange={handleChange}
                className="w-full p-2 mt-1 rounded-md border border-gray-300"
                required
              />
              <span className="absolute inset-y-0 right-0 pr-3 py-1 flex items-center cursor-pointer" onClick={togglePasswordVisibility}>
                {passwordShown ? 
                  <Image src="/hide.svg" alt="Hide password" width={24} height={24} /> : 
                  <Image src="/show.svg" alt="Show password" width={24} height={24} />
                }
              </span>
            
            </div>
            <div>
              <label htmlFor="mfa_code" className="text-sm font-bold">MFA Code (Optional)</label>
              <input
                type="text"
                name="mfa_code"
                id="mfa_code"
                value={loginData.mfa_code}
                onChange={handleChange}
                className="w-full p-2 mt-1 rounded-md border border-gray-300"
              />
              <p className="text-xs mt-1"><em>Enter your MFA code here if you have enabled multi-factor authentication.</em></p>
            </div>
            <button
              type="submit"
              className="w-full p-2 mt-4 bg-black text-white rounded-md hover:bg-opacity-90"
            >
              Log In
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
