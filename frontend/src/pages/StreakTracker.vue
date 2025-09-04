<template>
	<div class="container mx-auto px-4 py-6">
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">Streak Tracker</h1>
			<p class="text-gray-600">Keep your learning momentum going with daily streaks</p>
		</div>

		<!-- Current Streak Overview -->
		<div class="bg-gradient-to-r from-orange-500 to-red-500 rounded-lg p-8 text-white mb-8">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-2xl font-bold mb-2">Current Streak</h2>
					<div class="flex items-baseline space-x-2">
						<span class="text-6xl font-bold">{{ streakStats?.current_streak || 0 }}</span>
						<span class="text-xl opacity-90">days</span>
					</div>
					<p class="text-orange-100 mt-2">
						{{ getStreakMessage() }}
					</p>
				</div>
				<div class="text-8xl opacity-80">
					{{ getStreakEmoji() }}
				</div>
			</div>
		</div>

		<!-- Streak Stats Cards -->
		<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow-sm border p-6">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold text-gray-900 mb-1">Longest Streak</h3>
						<p class="text-3xl font-bold text-blue-600">{{ streakStats?.longest_streak || 0 }}</p>
						<p class="text-sm text-gray-500">days</p>
					</div>
					<div class="text-3xl">🏆</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow-sm border p-6">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold text-gray-900 mb-1">Total Active Days</h3>
						<p class="text-3xl font-bold text-green-600">{{ streakStats?.total_active_days || 0 }}</p>
						<p class="text-sm text-gray-500">days</p>
					</div>
					<div class="text-3xl">📅</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow-sm border p-6">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold text-gray-900 mb-1">This Week</h3>
						<p class="text-3xl font-bold text-purple-600">{{ weeklyStreak }}</p>
						<p class="text-sm text-gray-500">days active</p>
					</div>
					<div class="text-3xl">📊</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow-sm border p-6">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold text-gray-900 mb-1">Streak Freezes</h3>
						<p class="text-3xl font-bold text-cyan-600">{{ streakStats?.freeze_count || 0 }}</p>
						<p class="text-sm text-gray-500">available</p>
					</div>
					<div class="text-3xl">🧊</div>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Streak Calendar -->
			<div class="bg-white rounded-lg shadow-sm border">
				<div class="p-6 border-b">
					<h2 class="text-xl font-semibold text-gray-900">Activity Calendar</h2>
					<p class="text-sm text-gray-600 mt-1">Your learning activity over the past 30 days</p>
				</div>
				
				<div class="p-6">
					<div v-if="streakHistoryResource.loading" class="animate-pulse">
						<div class="grid grid-cols-7 gap-2">
							<div v-for="i in 35" :key="i" class="w-8 h-8 bg-gray-200 rounded"></div>
						</div>
					</div>
					
					<div v-else>
						<!-- Calendar Header -->
						<div class="grid grid-cols-7 gap-2 mb-2">
							<div v-for="day in ['S', 'M', 'T', 'W', 'T', 'F', 'S']" :key="day" class="text-center text-xs font-medium text-gray-500 p-2">
								{{ day }}
							</div>
						</div>
						
						<!-- Calendar Grid -->
						<div class="grid grid-cols-7 gap-2">
							<div
								v-for="day in calendarDays"
								:key="day.date"
								:class="[
									'w-8 h-8 rounded flex items-center justify-center text-xs font-medium transition-colors cursor-pointer',
									day.isActive ? 'bg-orange-500 text-white' :
									day.isToday ? 'bg-blue-100 text-blue-800 border-2 border-blue-500' :
									day.isCurrentMonth ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' :
									'bg-gray-50 text-gray-400'
								]"
								:title="day.isActive ? `Active on ${day.date}` : `No activity on ${day.date}`"
							>
								{{ day.day }}
							</div>
						</div>
						
						<!-- Legend -->
						<div class="flex items-center justify-between mt-4 text-xs text-gray-600">
							<span>Less active</span>
							<div class="flex items-center space-x-1">
								<div class="w-3 h-3 bg-gray-100 rounded"></div>
								<div class="w-3 h-3 bg-orange-200 rounded"></div>
								<div class="w-3 h-3 bg-orange-400 rounded"></div>
								<div class="w-3 h-3 bg-orange-500 rounded"></div>
							</div>
							<span>More active</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Streak Milestones & Tips -->
			<div class="space-y-6">
				<!-- Streak Milestones -->
				<div class="bg-white rounded-lg shadow-sm border">
					<div class="p-6 border-b">
						<h2 class="text-xl font-semibold text-gray-900">Streak Milestones</h2>
					</div>
					
					<div class="p-6 space-y-4">
						<div
							v-for="milestone in streakMilestones"
							:key="milestone.days"
							:class="[
								'flex items-center space-x-4 p-4 rounded-lg border-2 transition-colors',
								milestone.achieved ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
							]"
						>
							<div
								:class="[
									'w-12 h-12 rounded-full flex items-center justify-center text-2xl',
									milestone.achieved ? 'bg-green-100' : 'bg-gray-100'
								]"
							>
								{{ milestone.achieved ? '✅' : milestone.emoji }}
							</div>
							<div class="flex-1">
								<h3 class="font-semibold text-gray-900">{{ milestone.title }}</h3>
								<p class="text-sm text-gray-600">{{ milestone.description }}</p>
								<div class="text-xs text-gray-500 mt-1">{{ milestone.days }} day streak</div>
							</div>
							<div v-if="milestone.achieved" class="text-green-600 font-medium text-sm">
								Achieved!
							</div>
						</div>
					</div>
				</div>

				<!-- Streak Tips -->
				<div class="bg-white rounded-lg shadow-sm border">
					<div class="p-6 border-b">
						<h2 class="text-xl font-semibold text-gray-900">Streak Tips</h2>
					</div>
					
					<div class="p-6 space-y-4">
						<div v-for="tip in streakTips" :key="tip.title" class="flex items-start space-x-3">
							<div class="text-2xl">{{ tip.emoji }}</div>
							<div>
								<h3 class="font-medium text-gray-900">{{ tip.title }}</h3>
								<p class="text-sm text-gray-600 mt-1">{{ tip.description }}</p>
							</div>
						</div>
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

// Streak stats resource
const streakStatsResource = createResource({
	url: 'lms.api.get_user_streak_stats',
	auto: true
})

// Streak history resource
const streakHistoryResource = createResource({
	url: 'lms.api.get_user_streak_history',
	params: {
		days: 30
	},
	auto: true
})

const streakStats = computed(() => {
	return streakStatsResource.data
})

const streakHistory = computed(() => {
	return streakHistoryResource.data || []
})

const weeklyStreak = computed(() => {
	const today = new Date()
	const weekStart = new Date(today)
	weekStart.setDate(today.getDate() - today.getDay())
	
	return streakHistory.value.filter(record => {
		const recordDate = new Date(record.activity_date)
		return recordDate >= weekStart && recordDate <= today && record.is_active
	}).length
})

const calendarDays = computed(() => {
	const today = new Date()
	const startDate = new Date(today)
	startDate.setDate(today.getDate() - 30)
	
	// Get first day of the month to show
	const firstDay = new Date(startDate.getFullYear(), startDate.getMonth(), 1)
	const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
	
	// Adjust to start from Sunday
	const calendarStart = new Date(firstDay)
	calendarStart.setDate(firstDay.getDate() - firstDay.getDay())
	
	const days = []
	const current = new Date(calendarStart)
	
	while (current <= lastDay || days.length % 7 !== 0) {
		const dateStr = current.toISOString().split('T')[0]
		const isActive = streakHistory.value.some(record => 
			record.activity_date === dateStr && record.is_active
		)
		
		days.push({
			date: dateStr,
			day: current.getDate(),
			isActive,
			isToday: dateStr === today.toISOString().split('T')[0],
			isCurrentMonth: current.getMonth() === today.getMonth()
		})
		
		current.setDate(current.getDate() + 1)
	}
	
	return days
})

const streakMilestones = computed(() => {
	const currentStreak = streakStats.value?.current_streak || 0
	const longestStreak = streakStats.value?.longest_streak || 0
	
	return [
		{
			days: 3,
			title: 'Getting Started',
			description: 'Complete your first 3-day streak',
			emoji: '🌱',
			achieved: longestStreak >= 3
		},
		{
			days: 7,
			title: 'Week Warrior',
			description: 'Maintain a 7-day learning streak',
			emoji: '⚡',
			achieved: longestStreak >= 7
		},
		{
			days: 30,
			title: 'Monthly Master',
			description: 'Achieve a 30-day streak',
			emoji: '🔥',
			achieved: longestStreak >= 30
		},
		{
			days: 100,
			title: 'Century Champion',
			description: 'Reach the legendary 100-day streak',
			emoji: '👑',
			achieved: longestStreak >= 100
		}
	]
})

const streakTips = [
	{
		emoji: '⏰',
		title: 'Set a Daily Schedule',
		description: 'Choose a consistent time each day for learning to build a habit.'
	},
	{
		emoji: '🎯',
		title: 'Start Small',
		description: 'Even 10-15 minutes of learning counts towards your streak.'
	},
	{
		emoji: '📱',
		title: 'Use Reminders',
		description: 'Set up notifications to remind you to maintain your streak.'
	},
	{
		emoji: '🧊',
		title: 'Use Streak Freezes',
		description: 'Save streak freezes for days when you absolutely cannot learn.'
	}
]

const getStreakMessage = () => {
	const streak = streakStats.value?.current_streak || 0
	
	if (streak === 0) {
		return "Start your learning journey today!"
	} else if (streak < 7) {
		return "Great start! Keep it going!"
	} else if (streak < 30) {
		return "You're on fire! Amazing consistency!"
	} else if (streak < 100) {
		return "Incredible dedication! You're a learning machine!"
	} else {
		return "Legendary streak! You're an inspiration!"
	}
}

const getStreakEmoji = () => {
	const streak = streakStats.value?.current_streak || 0
	
	if (streak === 0) {
		return "🌟"
	} else if (streak < 7) {
		return "🔥"
	} else if (streak < 30) {
		return "⚡"
	} else if (streak < 100) {
		return "🚀"
	} else {
		return "👑"
	}
}

onMounted(() => {
	streakStatsResource.reload()
	streakHistoryResource.reload()
})
</script>