import React from 'react'
import { useAuth } from '../store'
import Landing from './Landing'
import Dashboard from './Dashboard'

function Home() {
  const { token } = useAuth()
  return token ? <Dashboard /> : <Landing />
}

export default Home
