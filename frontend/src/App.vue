<script setup>
import { onMounted, ref } from 'vue'

const apiUrl = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:${import.meta.env.VITE_API_PORT || '8000'}`
const status = ref('Checking connection...')
const error = ref('')

async function checkConnection() {
  status.value = 'Checking connection...'
  error.value = ''
  try {
    const response = await fetch(`${apiUrl.replace(/\/$/, '')}/health`, {
      headers: { 'X-Frontend-Check': 'vue' },
    })
    if (!response.ok) {
      throw new Error(`API returned HTTP ${response.status}`)
    }
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error('Unexpected health response')
    }
    status.value = 'Connected to the backend'
  } catch (cause) {
    status.value = 'Connection failed'
    error.value = cause instanceof Error ? cause.message : String(cause)
  }
}

onMounted(checkConnection)
</script>

<template>
  <main>
    <h1>Blog API connection</h1>
    <p role="status">{{ status }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <button type="button" @click="checkConnection">Check again</button>
  </main>
</template>
