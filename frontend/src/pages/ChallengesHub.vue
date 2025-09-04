<template>
	<div class="container mx-auto px-4 py-6">
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">Challenges Hub</h1>
			<p class="text-gray-600">Take on challenges to earn extra points and achievements</p>
		</div>

		<!-- Challenge Filters -->
		<div class="mb-6">
			<div class="flex flex-wrap gap-2">
				<button
					v-for="filter in filters"
					:key="filter.value"
					@click="selectedFilter = filter.value"
					:class="[
						'px-4 py-2 rounded-lg font-medium transition-colors',
						selectedFilter === filter.value
							? 'bg-blue-600 text-white'
							: 'bg-gray-100 text-gray-700 hover:bg-gray-200'
					]"
				>
					{{ filter.label }}
				</button>
			</div>
		</div>

		<!-- User Challenge Stats -->
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
			<div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
				<div class="text-2xl font-bold text-blue-600">{{ challengeStats.active || 0 }}</div>
				<div class="text-sm text-blue-700">Active Challenges</div>
			</div>
			<div class="bg-green-50 rounded-lg p-4 border border-green-200">
				<div class="text-2xl font-bold text-green-600">{{ challengeStats.completed || 0 }}</div>
				<div class="text-sm text-green-700">Completed</div>
			</div>
			<div class="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
				<div class="text-2xl font-bold text-yellow-600">{{ challengeStats.points_earned || 0 }}</div>
				<div class="text-sm text-yellow-700">Points Earned</div>
			</div>
			<div class="bg-purple-50 rounded-lg p-4 border border-purple-200">
				<div class="text-2xl font-bold text-purple-600">{{ challengeStats.success_rate || 0 }}%</div>
				<div class="text-sm text-purple-700">Success Rate</div>
			</div>
		</div>

		<!-- Challenges Grid -->
		<div v-if="challengesResource.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			<div v-for="i in 6" :key="i" class="bg-white rounded-lg shadow-sm border p-6">
				<div class="animate-pulse">
					<div class="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
					<div class="h-3 bg-gray-200 rounded w-full mb-2"></div>
					<div class="h-3 bg-gray-200 rounded w-2/3 mb-4"></div>
					<div class="h-2 bg-gray-200 rounded w-full mb-4"></div>
					<div class="h-8 bg-gray-200 rounded w-1/2"></div>
				</div>
			</div>
		</div>

		<div v-else-if="filteredChallenges.length === 0" class="text-center py-12">
			<div class="text-6xl mb-4">🎯</div>
			<h3 class="text-xl font-semibold text-gray-900 mb-2">No challenges found</h3>
			<p class="text-gray-600">Try changing your filter or check back later for new challenges.</p>
		</div>

		<div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			<div
				v-for="challenge in filteredChallenges"
				:key="challenge.name"
				class="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow"
			>
				<div class="p-6">
					<!-- Challenge Header -->
					<div class="flex items-start justify-between mb-4">
						<div class="flex-1">
							<h3 class="text-lg font-semibold text-gray-900 mb-1">{{ challenge.title }}</h3>
							<div class="flex items-center space-x-2 mb-2">
								<span
									:class="[
										'px-2 py-1 rounded-full text-xs font-medium',
										challenge.challenge_type === 'daily' ? 'bg-blue-100 text-blue-800' :
										challenge.challenge_type === 'weekly' ? 'bg-green-100 text-green-800' :
										challenge.challenge_type === 'monthly' ? 'bg-purple-100 text-purple-800' :
										'bg-gray-100 text-gray-800'
									]"
								>
									{{ challenge.challenge_type }}
								</span>
								<span class="text-sm text-gray-500">{{ challenge.points_reward }} pts</span>
							</div>
						</div>
						<div
							:class="[
								'px-2 py-1 rounded-full text-xs font-medium',
								getChallengeStatus(challenge) === 'completed' ? 'bg-green-100 text-green-800' :
								getChallengeStatus(challenge) === 'active' ? 'bg-yellow-100 text-yellow-800' :
								getChallengeStatus(challenge) === 'available' ? 'bg-blue-100 text-blue-800' :
								'bg-gray-100 text-gray-800'
							]"
						>
							{{ getStatusLabel(getChallengeStatus(challenge)) }}
						</div>
					</div>

					<!-- Challenge Description -->
					<p class="text-gray-600 text-sm mb-4 line-clamp-2">{{ challenge.description }}</p>

					<!-- Challenge Progress -->
					<div v-if="challenge.participation" class="mb-4">
						<div class="flex items-center justify-between mb-2">
							<span class="text-sm font-medium text-gray-700">Progress</span>
							<span class="text-sm text-gray-500">
								{{ challenge.participation.current_value }} / {{ challenge.target_value }}
							</span>
						</div>
						<div class="w-full bg-gray-200 rounded-full h-2">
							<div
								class="bg-blue-600 h-2 rounded-full transition-all duration-300"
								:style="{ width: Math.min((challenge.participation.current_value / challenge.target_value) * 100, 100) + '%' }"
							></div>
						</div>
					</div>

					<!-- Challenge Dates -->
					<div class="text-xs text-gray-500 mb-4">
						<div v-if="challenge.start_date">Starts: {{ formatDate(challenge.start_date) }}</div>
						<div v-if="challenge.end_date">Ends: {{ formatDate(challenge.end_date) }}</div>
					</div>

					<!-- Challenge Actions -->
					<div class="flex space-x-2">
						<button
							v-if="getChallengeStatus(challenge) === 'available'"
							@click="joinChallenge(challenge)"
							class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
							:disabled="joiningChallenge === challenge.name"
						>
							<span v-if="joiningChallenge === challenge.name">Joining...</span>
							<span v-else>Join Challenge</span>
						</button>
						<button
							v-else-if="getChallengeStatus(challenge) === 'active'"
							class="flex-1 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg font-medium cursor-default"
							disabled
						>
							In Progress
						</button>
						<button
							v-else-if="getChallengeStatus(challenge) === 'completed'"
							class="flex-1 bg-green-100 text-green-800 px-4 py-2 rounded-lg font-medium cursor-default"
							disabled
						>
							✓ Completed
						</button>
						<button
							v-else
							class="flex-1 bg-gray-100 text-gray-500 px-4 py-2 rounded-lg font-medium cursor-default"
							disabled
						>
							Unavailable
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const { $session } = sessionStore()

const selectedFilter = ref('all')
const joiningChallenge = ref(null)

const filters = [
	{ value: 'all', label: 'All Challenges' },
	{ value: 'available', label: 'Available' },
	{ value: 'active', label: 'Active' },
	{ value: 'completed', label: 'Completed' },
	{ value: 'daily', label: 'Daily' },
	{ value: 'weekly', label: 'Weekly' },
	{ value: 'monthly', label: 'Monthly' }
]

// Challenges resource
const challengesResource = createResource({
	url: 'lms.api.get_challenges',
	auto: true
})

// Challenge stats resource
const challengeStatsResource = createResource({
	url: 'lms.api.get_user_challenge_stats',
	auto: true
})

// Join challenge resource
const joinChallengeResource = createResource({
	url: 'lms.api.join_challenge',
	method: 'POST'
})

const challenges = computed(() => {
	return challengesResource.data || []
})

const challengeStats = computed(() => {
	return challengeStatsResource.data || {}
})

const filteredChallenges = computed(() => {
	if (selectedFilter.value === 'all') {
		return challenges.value
	}
	
	return challenges.value.filter(challenge => {
		const status = getChallengeStatus(challenge)
		
		if (['available', 'active', 'completed'].includes(selectedFilter.value)) {
			return status === selectedFilter.value
		}
		
		if (['daily', 'weekly', 'monthly'].includes(selectedFilter.value)) {
			return challenge.challenge_type === selectedFilter.value
		}
		
		return true
	})
})

const getChallengeStatus = (challenge) => {
	if (challenge.participation) {
		if (challenge.participation.status === 'completed') {
			return 'completed'
		}
		if (challenge.participation.status === 'active') {
			return 'active'
		}
	}
	
	const now = new Date()
	const startDate = challenge.start_date ? new Date(challenge.start_date) : null
	const endDate = challenge.end_date ? new Date(challenge.end_date) : null
	
	if (startDate && now < startDate) {
		return 'upcoming'
	}
	
	if (endDate && now > endDate) {
		return 'expired'
	}
	
	return 'available'
}

const getStatusLabel = (status) => {
	switch (status) {
		case 'available': return 'Available'
		case 'active': return 'Active'
		case 'completed': return 'Completed'
		case 'upcoming': return 'Upcoming'
		case 'expired': return 'Expired'
		default: return 'Unknown'
	}
}

const joinChallenge = async (challenge) => {
	joiningChallenge.value = challenge.name
	
	try {
		await joinChallengeResource.submit({
			challenge_name: challenge.name
		})
		
		// Reload challenges to update participation status
		await challengesResource.reload()
		await challengeStatsResource.reload()
		
		// Show success message (you might want to use a toast notification)
		console.log('Successfully joined challenge:', challenge.title)
	} catch (error) {
		console.error('Failed to join challenge:', error)
		// Show error message
	} finally {
		joiningChallenge.value = null
	}
}

const formatDate = (dateString) => {
	const date = new Date(dateString)
	return date.toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		year: 'numeric'
	})
}

onMounted(() => {
	challengesResource.reload()
	challengeStatsResource.reload()
})
</script>

<style scoped>
.line-clamp-2 {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}
</style>