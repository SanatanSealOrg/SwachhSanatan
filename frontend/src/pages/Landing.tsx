import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const pledgeLines = [
  'I will not throw waste on roads, parks, or water bodies.',
  'I will report waste and sanitation issues I see in my neighborhood.',
  'I will encourage at least one family member or neighbor to join Nagar Seva.',
  'I will follow up until every report I file is actually resolved.',
]

const usps = [
  {
    icon: '📸',
    title: 'Report in seconds',
    desc: 'Snap a photo of an overflowing bin or illegal dumping — your GPS location is captured automatically, no address typing needed.',
    color: 'blue',
  },
  {
    icon: '🤖',
    title: 'AI-ranked response',
    desc: 'Every report is triaged and routed to the right ward officer, prioritized by severity so the worst hotspots get cleared first.',
    color: 'purple',
  },
  {
    icon: '📊',
    title: 'Public accountability',
    desc: 'Ward-by-ward cleanliness scores and complaint trends are open to every citizen — sunlight keeps the system honest.',
    color: 'green',
  },
  {
    icon: '🔎',
    title: 'Track to resolution',
    desc: 'Follow any ticket from submission to clean-up with a simple ticket number — no phone calls, no follow-ups needed.',
    color: 'blue',
  },
]

const steps = [
  { n: '1', title: 'Report', desc: 'Citizens photograph waste issues with location tagged automatically.' },
  { n: '2', title: 'Route & Prioritize', desc: 'AI classifies the issue and ranks it for the nearest ward officer.' },
  { n: '3', title: 'Resolve & Verify', desc: 'Officers act, citizens confirm resolution — closing the loop transparently.' },
]

const colorClasses: Record<string, string> = {
  blue: 'bg-blue-50 border-blue-500 text-blue-700',
  purple: 'bg-purple-50 border-purple-500 text-purple-700',
  green: 'bg-green-50 border-green-500 text-green-700',
}

function Landing() {
  const navigate = useNavigate()
  const [pledged, setPledged] = useState(false)

  const goSignUp = () => navigate('/login', { state: { mode: 'register', from: '/report' } })
  const goTrack = () => navigate('/track')

  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="text-center pt-2 pb-6">
        <p className="text-green-700 font-semibold tracking-wide uppercase text-sm mb-3">
          🇮🇳 In the spirit of Swachh Bharat Mission &amp; Swasth Nagarik
        </p>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-4">
          Nagar Seva
        </h1>
        <p className="text-xl text-green-700 font-medium mb-4">
          Technology for cleaner cities, powered by every citizen.
        </p>
        <p className="text-gray-600 max-w-2xl mx-auto mb-8">
          Your neighborhood won't clean itself. Every dirty corner you report gets AI-routed to
          the right officer and tracked in the open — and your first report takes under a
          minute.
        </p>
        <div className="flex flex-wrap gap-4 justify-center mb-3">
          <button
            onClick={goSignUp}
            className="bg-green-600 text-white px-8 py-4 rounded-lg font-bold text-lg shadow-lg hover:bg-green-700 hover:scale-105 transition"
          >
            🚀 Sign Up &amp; Report Your First Issue
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Free forever · Takes under 60 seconds · No paperwork, just a photo
        </p>
        <button onClick={goTrack} className="text-green-700 font-medium hover:underline text-sm">
          🔎 Already reported something? Track your complaint
        </button>
      </section>

      {/* Pledge */}
      <section className="bg-green-50 border-2 border-green-200 rounded-lg shadow p-8 max-w-2xl mx-auto text-center">
        <p className="text-green-700 font-semibold uppercase tracking-wide text-sm mb-2">
          🇮🇳 Take the Swachhata Pledge
        </p>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Pledge, then join the movement</h2>
        <ul className="text-left space-y-3 mb-8">
          {pledgeLines.map((line) => (
            <li key={line} className="flex gap-3 items-start text-gray-700">
              <span className="text-green-600 font-bold">✓</span>
              <span>{line}</span>
            </li>
          ))}
        </ul>
        <label className="flex items-center gap-3 justify-center mb-6 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={pledged}
            onChange={(e) => setPledged(e.target.checked)}
            className="w-5 h-5 accent-green-600"
          />
          <span className="text-gray-800 font-medium">I take this pledge for a cleaner Nagar</span>
        </label>
        <button
          onClick={goSignUp}
          disabled={!pledged}
          className="bg-green-600 text-white px-8 py-4 rounded-lg font-bold text-lg shadow-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          🤝 I Pledge — Sign Up &amp; Join the Movement
        </button>
      </section>

      {/* Direct conversion nudge */}
      <section className="bg-white rounded-lg shadow-lg p-8 text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Be the citizen who spoke up</h2>
        <p className="text-gray-600 max-w-xl mx-auto mb-6">
          Someone has to be the first to flag that overflowing bin or dumping spot near you.
          Thousands of small reports are what turn into clean, accountable wards — start yours
          today.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-left">
          <div className="flex gap-3 items-start">
            <span className="text-2xl">📸</span>
            <div>
              <p className="font-semibold text-gray-800">Snap</p>
              <p className="text-sm text-gray-600">A photo of the issue, wherever you are.</p>
            </div>
          </div>
          <div className="flex gap-3 items-start">
            <span className="text-2xl">📍</span>
            <div>
              <p className="font-semibold text-gray-800">Send</p>
              <p className="text-sm text-gray-600">Location is auto-tagged, no form-filling.</p>
            </div>
          </div>
          <div className="flex gap-3 items-start">
            <span className="text-2xl">✅</span>
            <div>
              <p className="font-semibold text-gray-800">See it fixed</p>
              <p className="text-sm text-gray-600">Track your ticket until it's resolved.</p>
            </div>
          </div>
        </div>
        <button
          onClick={goSignUp}
          className="bg-green-600 text-white px-8 py-3 rounded-lg font-bold shadow hover:bg-green-700 transition"
        >
          Sign Up Now — Submit Your First Report
        </button>
      </section>

      {/* Impact strip */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Ward-level transparency', value: 'Every ward, scored' },
          { label: 'From report to resolution', value: 'Fully tracked' },
          { label: 'Prioritization', value: 'AI-assisted' },
          { label: 'Access', value: 'Open to all citizens' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-lg font-bold text-green-700">{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </section>

      {/* USPs */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-2">Why Nagar Seva</h2>
        <p className="text-gray-600 text-center mb-10 max-w-xl mx-auto">
          Built to make civic participation effortless and civic response accountable.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {usps.map((u) => (
            <div
              key={u.title}
              className={`p-6 rounded-lg border-l-4 ${colorClasses[u.color]} bg-opacity-60`}
            >
              <h3 className="text-lg font-bold mb-2">
                {u.icon} {u.title}
              </h3>
              <p className="text-gray-600 text-sm">{u.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-10">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((s) => (
            <div key={s.n} className="text-center">
              <div className="w-12 h-12 rounded-full bg-green-600 text-white font-bold flex items-center justify-center mx-auto mb-4 text-lg">
                {s.n}
              </div>
              <h3 className="font-bold text-gray-800 mb-2">{s.title}</h3>
              <p className="text-gray-600 text-sm">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Community impact / final call to action */}
      <section className="text-center bg-gradient-to-r from-green-600 to-green-700 rounded-lg shadow-lg p-10 text-white">
        <h2 className="text-2xl font-bold mb-3">A cleaner ward starts with your report</h2>
        <p className="max-w-xl mx-auto mb-6 text-green-50">
          Swachh Bharat and a healthy, Swasth Nagarik begin with everyday citizens who refuse to
          look away from a problem. Every report you file makes your neighborhood's cleanliness
          measurable — and every measurement makes it harder to ignore. Don't wait for someone
          else to file it.
        </p>
        <button
          onClick={goSignUp}
          className="bg-white text-green-700 px-8 py-4 rounded-lg font-bold text-lg shadow hover:bg-green-50 hover:scale-105 transition"
        >
          Sign Up &amp; Join the Movement — Report Now
        </button>
        <p className="text-green-100 text-xs mt-3">It takes less time than reading this page.</p>
      </section>
    </div>
  )
}

export default Landing
