<template>
	<div class="container mx-auto px-4 py-6">
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">Leaderboard</h1>
			<p class="text-gray-600">See how you rank among other learners</p>
		</div>

		<!-- Period Selector -->
		<div class="mb-6">
			<div class="flex space-x-2">
				<button
					v-for="period in periods"
					:key="period.value"
					@click="selectedPeriod = period.value"
					:class="[
						'px-4 py-2 rounded-lg font-medium transition-colors',
						selectedPeriod === period.value
							? 'bg-blue-600 text-white'
							: 'bg-gray-100 text-gray-700 hover:bg-gray-200'
					]"
				>
					{{ period.label }}
				</button>
			</div>
		</div>

		<!-- Current User Rank Card -->
		<div v-if="currentUserRank" class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white mb-6">
			<div class="flex items-center justify-between">
				<div>
					<h3 class="text-lg font-semibold mb-1">Your Current Rank</h3>
					<p class="text-blue-100">{{ selectedPeriod }} leaderboard</p>
				</div>
				<div class="text-right">
					<div class="text-3xl font-bold">#{{ currentUserRank.rank }}</div>
					<div class="text-blue-100">{{ currentUserRank.points }} points</div>
				</div>
			</div>
		</div>

		<!-- Leaderboard List -->
		<div class="bg-white rounded-lg shadow-sm border">
			<div class="p-6 border-b">
				<h2 class="text-xl font-semibold text-gray-900">Top Performers</h2>
			</div>
			
			<div v-if="leaderboardResource.loading" class="p-6">
				<div class="animate-pulse space-y-4">
					<div v-for="i in 10" :key="i" class="flex items-center space-x-4">
						<div class="w-8 h-8 bg-gray-200 rounded-full"></div>
						<div class="flex-1 space-y-2">
							<div class="h-4 bg-gray-200 rounded w-1/4"></div>
							<div class="h-3 bg-gray-200 rounded w-1/6"></div>
						</div>
						<div class="h-4 bg-gray-200 rounded w-16"></div>
					</div>
				</div>
			</div>

			<div v-else-if="leaderboardData.length === 0" class="p-6 text-center text-gray-500">
				<p>No leaderboard data available for this period.</p>
			</div>

			<div v-else class="divide-y divide-gray-100">
				<div
					v-for="(entry, index) in leaderboardData"
					:key="entry.name"
					:class="[
						'p-6 flex items-center justify-between hover:bg-gray-50 transition-colors',
						entry.user === $session.user ? 'bg-blue-50 border-l-4 border-blue-500' : ''
					]"
				>
					<div class="flex items-center space-x-4">
						<!-- Rank Badge -->
						<div
							:class="[
								'w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm',
								entry.rank === 1 ? 'bg-yellow-100 text-yellow-800' :
								entry.rank === 2 ? 'bg-gray-100 text-gray-800' :
								entry.rank === 3 ? 'bg-orange-100 text-orange-800' :
								'bg-blue-100 text-blue-800'
							]"
						>
							{{ entry.rank }}
						</div>

						<!-- User Info -->
						<div>
							<div class="font-semibold text-gray-900">
								{{ entry.full_name || entry.user }}
								<span v-if="entry.user === $session.user" class="ml-2 text-sm text-blue-600 font-medium">(You)</span>
							</div>
							<div class="text-sm text-gray-500">{{ entry.user }}</div>
						</div>
					</div>

					<!-- Points -->
					<div class="text-right">
						<div class="font-bold text-lg text-gray-900">{{ entry.points }}</div>
						<div class="text-sm text-gray-500">points</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const { $session } = sessionStore()

const selectedPeriod = ref('weekly')
const periods = [
	{ value: 'daily', label: 'Daily' },
	{ value: 'weekly', label: 'Weekly' },
	{ value: 'monthly', label: 'Monthly' },
	{ value: 'all_time', label: 'All Time' }
]

// Leaderboard data resource
const leaderboardResource = createResource({
	url: 'lms.api.get_leaderboard',
	params: {
		period: selectedPeriod.value,
		limit: 50
	},
	auto: true
})

// Current user rank resource
const userRankResource = createResource({
	url: 'lms.api.get_user_rank',
	params: {
		period: selectedPeriod.value
	},
	auto: true
})

const leaderboardData = computed(() => {
	return leaderboardResource.data || []
})

const currentUserRank = computed(() => {
	return userRankResource.data
})

// Watch for period changes and reload data
watch(selectedPeriod, (newPeriod) => {
	leaderboardResource.update({
		params: {
			period: newPeriod,
			limit: 50
		}
	})
	leaderboardResource.reload()
	
	userRankResource.update({
		params: {
			period: newPeriod
		}
	})
	userRankResource.reload()
})

onMounted(() => {
	leaderboardResource.reload()
	userRankResource.reload()
})
</script>